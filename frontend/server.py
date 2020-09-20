"""The main flask app."""
from collections import defaultdict
from datetime import datetime
from io import BytesIO
import os
from typing import List
import urllib

import flask
from flask import (
    Flask, Response, jsonify, make_response, redirect, render_template, request)

import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

from db.models import (
    ALL_MODELS,
    BacktestResultModel,
    DataGrabberModel,
    HyperQuestResultModel,
    PredictorPerformanceResultModel,
    RunSet,
    RunSetEntry,
    TrainedNetworkDataModel,
    get_model_obj_instantiated_fields,
    get_hyperparams_for_hyperquest)
from vinci.db import connection
import db.login_file
from vinci.plot_tools import plot_whatever
from predictor_brain import (Predictor, load_net)
from training_data import (generate_training_data_from_grabber)


# Connect to the database.
if not connection.get_peewee_db():
    connection.connect(db.login_file.full_path, ALL_MODELS)


def pretty_datetime(dt: datetime) -> str:
    """Format a datetime string nicely.

    Args:
        datetime: The datetime object.

    Return:
        The formatted version, like 2019-01-01 11:31pm
    """
    return dt.strftime('%Y-%m-%d %I:%M%p')


def dir_last_updated(folder='static'):
    """This is super useful for getting the site to not cache our custom Javascript files, so
    we can let the browser cache all the big framework ones, but reload ours properly when they
    change.

    https://stackoverflow.com/questions/41144565/flask-does-not-see-change-in-js-file

    Args:
        folder: The folder to look into.

    Return:
        The most recent modified time of any file in the given folder.
    """
    return str(max(os.path.getmtime(os.path.join(root_path, f))
               for root_path, dirs, files in os.walk(folder)
               for f in files))


# Create the Flask app.
app = Flask('StockBot server')


def sidebar_info(
        runsets_active: bool = False,
        greatest_hits_active: bool = False,
        hyperquests_active: bool = False):
    """This generates the jinja variables that base.html needs to highlight items in the
    left-side bar."""
    def active_string(val: bool):
        return 'active' if val else ''

    return {
        'runsets_active': active_string(runsets_active),
        'greatest_hits_active': active_string(greatest_hits_active),
        'hyperquests_active': active_string(hyperquests_active)
    }


# Handle initial visits to the site.
@app.route('/')
def root():
    return redirect('/runsets')

# Handle hyperquest stuff.
@app.route('/hyperquest/')
def hyperquest():
    return render_template(
        'hyperquest.html',
        **sidebar_info(hyperquests_active=True),
        dir_last_updated=dir_last_updated())


@app.route('/runsets')
def runsets():
    return render_template(
        'runsets.html',
        **sidebar_info(runsets_active=True),
        dir_last_updated=dir_last_updated())


@app.route('/runset/<id>')
def runset(id: int):
    # Detect if we're showing the greatest hits page.
    if int(id) == 277:
        runsets_active = False
        greatest_hits_active = True
        runset_title = f'Stockbot\'s Greatest Hits!'
        runset_image = '/static/greatest_hits.jpg'
    else:
        runsets_active = True
        greatest_hits_active = False
        runset_title = f'Runset {id}'
        runset_image = None


    num_hqrs = request.args.get('num', 100)

    # provide a url that will serve as a replacement for the url input. This is useful for informing
    # the user of auto-populated default values
    replace_url = f"{id}?num={num_hqrs}"

    return render_template(
        'runset.html',
        runset_id=id,
        num_hqrs=num_hqrs,
        replace_url=replace_url,
        runset_title=runset_title,
        runset_image=runset_image,
        **sidebar_info(runsets_active=runsets_active, greatest_hits_active=greatest_hits_active),
        dir_last_updated=dir_last_updated())


@app.route('/datagrabber/<id>')
def datagrabber(id: int):
    return render_template(
        'datagrabber.html',
        datagrabber_id=id,
        dir_last_updated=dir_last_updated())

@app.route('/hqresult/<id>')
def hqresult(id: int):
    return render_template(
        'hqresult.html',
        hqresult_id=id,
        dir_last_updated=dir_last_updated())

@app.route('/compare_hyperquest_lists')
def compare_hyperquest_lists():
    list1 = urllib.parse.unquote(request.args.get('list1')).split(',')
    list2 = urllib.parse.unquote(request.args.get('list2')).split(',')
    return render_template(
        'compare_hyperquest_lists.html',
        title1=list1[0],
        title2=list2[0],
        list1=[int(x) for x in list1[1:]],
        list2=[int(x) for x in list2[1:]],
        dir_last_updated=dir_last_updated())


def runset_comparison_internal(
        runset_1_id: str,
        runset_2_id: str) -> flask.Response:
    """
    Args:
        runset_1_id: The first runset in the comparison.
        runset_2_id: The second runset in the comparison.

    Return:
        A response object.
    """

    return render_template(
        'runset_comparison.html',
        runset_1_id=runset_1_id,
        runset_2_id=runset_2_id,
        dir_last_updated=dir_last_updated())

# Handle reports stuff.
@app.route('/report/runset_comparison')
def runset_comparison():
    return runset_comparison_internal(
        request.args.get('runset_1_id'),
        request.args.get('runset_2_id'))



def format_for_hyperquest_list(hyperquests):
    """
    Args:
        hyperquests: The list of HyperQuestResultModel objects.

    Return:
        JSON that can be fed into a HyperquestList on the client.
    """
    ret = []
    for hq in hyperquests:
        pred_result = hq.predictor_perf_result_id

        ret.append({
            'id': hq.id,
            'predictor_table_name': hq.predictor_table_name,
            'grabber_id': hq.datagrabber_id.id,
            'creation_time': pretty_datetime(hq.creation_time),
            'num_epochs': len(pred_result.train_epoch_accuracies),
            'final_train_accuracy': pred_result.final_train_accuracy,
            'final_val_accuracy': pred_result.final_val_accuracy,
            'score': hq.predictor_perf_result_id.calculate_goodness_score()
            })
    return ret


@app.route('/api/get_hyperquests')
def get_hyperquests():
    ret = format_for_hyperquest_list(HyperQuestResultModel.select().order_by(
            HyperQuestResultModel.creation_time.desc()).join(
            PredictorPerformanceResultModel))
    return jsonify(ret)


@app.route('/api/get_runsets')
def get_runsets():
    """Get a list of the runsets."""
    ret = []
    for runset in RunSet.select().order_by(RunSet.id.desc()):
        ret.append({
            'id': runset.id,
            'tag': runset.tag,
            'comment': runset.comment,
            'command_line': runset.command_line,
            'num_hyperquests': RunSetEntry.select().where(
                RunSetEntry.runset == runset.id).count()
            })

    return jsonify(ret)


@app.route('/api/set_runset_tag/<runset_id>')
def set_runset_tag(runset_id):
    """Update the comment on a runset"""
    comment_parsed = request.args.get('value')
    runset = RunSet.get_by_id(runset_id)
    runset.tag = comment_parsed
    runset.save()
    return jsonify({'success': True})


@app.route('/api/set_runset_comment/<runset_id>')
def set_runset_comment(runset_id):
    """Update the comment on a runset"""
    comment_parsed = request.args.get('value')
    runset = RunSet.get_by_id(runset_id)
    runset.comment = comment_parsed
    runset.save()
    return jsonify({'success': True})


@app.route('/api/get_runset_info/<runset_id>')
def api_get_runset_info(runset_id: str):
    runset = RunSet.select().where(RunSet.id == runset_id).get()
    # throw in an arbitrarily large limit for now
    num_hqrs = request.args.get('num_hqrs', 10000)
    entries = RunSetEntry.select().where(RunSetEntry.runset == runset_id).join(
        HyperQuestResultModel).join(
            PredictorPerformanceResultModel).order_by(
                HyperQuestResultModel.id).limit(num_hqrs)

    return jsonify({
        'tag': runset.tag,
        'comment': runset.comment,
        'command_line': runset.command_line,
        'hyperquests': format_for_hyperquest_list([x.hq_result for x in entries])
        })


@app.route('/api/get_hyperquest_deets/<hq_id>')
def get_hyperquest_deets(hq_id):
    hq = HyperQuestResultModel.select().where(
            HyperQuestResultModel.id == hq_id) \
            .join(PredictorPerformanceResultModel) \
            .get()

    predictor: PredictorModel = get_hyperparams_for_hyperquest(hq)

    backtest_results = list(BacktestResultModel.select()
                        .where(BacktestResultModel.hyperquestresult_id == hq_id)
                        .order_by(BacktestResultModel.train_start_time))

    backtest_results_dict = [
        {
            'train_start': pretty_datetime(x.train_start_time),
            'train_end': pretty_datetime(x.train_end_time),
            'sim_start': pretty_datetime(x.sim_start_time),
            'sim_end': pretty_datetime(x.sim_end_time),
            'roi': x.roi
        }
        for x in backtest_results]

    return jsonify({
            'predictor_table_name': hq.predictor_table_name,
            'predictor_fields': get_model_obj_instantiated_fields(predictor),
            'backtest_results': backtest_results_dict
        })


def get_validation_correctness_over_time(hq_id: int) -> List[int]:
    """Get the values that can be used to plot validation correctness over time.

    Args:
        hq_id: The hyperquest ID

    Return:
        A list of the values to plot. Returns None if there is no data available.
    """
    try:
        hq = HyperQuestResultModel.select().where(
                HyperQuestResultModel.id == hq_id) \
                    .join(PredictorPerformanceResultModel) \
                    .get()
        result = hq.predictor_perf_result_id
        if not result.net_correctness_over_validation_examples:
            return None

        # The data just tells whether we were right or wrong on each example.
        # Do a walk where it goes up or down based on the rightness.
        current = 0
        val_falloff_over_time = [0]
        for sample in result.net_correctness_over_validation_examples:
            # Remap the [0, 1] range to [-1, 1] so the line goes up and down.
            current += ((sample * 2) - 1)
            val_falloff_over_time.append(current)

        return val_falloff_over_time
    except Exception as e:
        print('Got an exception: ' + type(e).__name__)
        if type(e).__name__ == 'HyperQuestResultModelDoesNotExist':
            # This means that it can't find either the hyperquest or
            # that the trained net isn't stored in the database.
            return None
        else:
            raise


@app.route('/api/plots/validation_correctness_over_time/<hq_id>')
def validation_correctness_over_time(hq_id):
    """
    """
    val_falloff_over_time = get_validation_correctness_over_time(int(hq_id))
    if not val_falloff_over_time:
        return Response("{}", status=404, mimetype='image/jpeg')

    num_samples = len(val_falloff_over_time)
    
    fig = plot_whatever(
        x_series=[range(num_samples)],
        y_series=[val_falloff_over_time],
        series_labels=['validation accuracy'],
        series_markers=['.', '.'],
        series_markersizes=[3, 3],
        series_istwin=[False, False],
        title=f'Validation accuracy over time for hyperquest {hq_id}',
        x_label='Validation set examples',
        fig_size=(8, 4),
        only_return_fig=True
    )

    return plot_to_png_response(fig)


@app.route('/api/plots/tiny/validation_correctness_over_time/<hq_id>')
def tiny_validation_correctness_over_time(hq_id):
    """
    """
    val_falloff_over_time = get_validation_correctness_over_time(int(hq_id))
    if not val_falloff_over_time:
        return Response("{}", status=404, mimetype='image/jpeg')

    num_samples = len(val_falloff_over_time)
    
    fig = plot_whatever(
        x_series=[range(num_samples)],
        y_series=[val_falloff_over_time],
        title=None,
        x_label=None,
        series_istwin=[False, False],
        fig_size=(1, 0.5),
        only_return_fig=True,
        show_ticks_and_labels=False
    )

    return plot_to_png_response(fig)


def plot_to_png_response(fig: plt.Figure) -> flask.Response:
    """Convert a plot to a flask Response that will show up to the browser like a png file.

    Args:
        fig: The plot to convert.

    Return:
        A flask.Response that you can return from a route handler.
    """
    # From https://gist.github.com/wilsaj/862153
    canvas = FigureCanvas(fig)
    png_output = BytesIO()
    canvas.print_png(png_output)
    response = make_response(png_output.getvalue())
    response.headers['Content-Type'] = 'image/png'
    return response


@app.route('/api/plots/hq_train_and_val_accuracies/<hq_id>')
def plot_hq_train_and_val_accuracies(hq_id):
    """
    """
    hq = HyperQuestResultModel.select().where(
            HyperQuestResultModel.id == hq_id).join(
            PredictorPerformanceResultModel).get()
    pred_result = hq.predictor_perf_result_id
    
    num_epochs = len(pred_result.train_epoch_accuracies)
    
    fig = plot_whatever(
        x_series=[range(num_epochs), range(num_epochs)],
        y_series=[pred_result.train_epoch_accuracies, pred_result.val_epoch_accuracies],
        series_labels=['train', 'test'],
        series_markers=['.', '.'],
        series_markersizes=[3, 3],
        series_istwin=[False, False],
        title=f'Train accuracies for hyperquest {hq_id}',
        x_label='Epochs',
        fig_size=(8, 4),
        only_return_fig=True
    )

    return plot_to_png_response(fig)


@app.route('/api/plots/tiny/hq_train_and_val_accuracies/<hq_id>')
def plot_tiny_hq_train_and_val_accuracies(hq_id):
    """
    """
    hq = HyperQuestResultModel.select().where(
            HyperQuestResultModel.id == hq_id).join(
            PredictorPerformanceResultModel).get()
    pred_result = hq.predictor_perf_result_id
    
    num_epochs = len(pred_result.train_epoch_accuracies)
    
    fig = plot_whatever(
        x_series=[range(num_epochs), range(num_epochs)],
        y_series=[pred_result.train_epoch_accuracies, pred_result.val_epoch_accuracies],
        title=None,
        x_label=None,
        series_istwin=[False, False],
        fig_size=(1, 0.5),
        only_return_fig=True,
        show_ticks_and_labels=False
    )

    return plot_to_png_response(fig)


@app.route('/api/get_hyperquests_by_runset/<runset_id>')
def get_hyperquests_by_runset(runset_id):
    """Get all the hyperquests, datagrabbers, and performance results for a certain runset.

    Args:
        runset_id: The id of the runset to get.

    Return:
        JSON with a list of objects that describe each hyperquest and its associated data.

        TODO: Clean this up. It's lame that each entry in the list reencodes the same runset.
              It should be something like:
                {
                    runset_id: <id>,
                    entries: [{...}, {...}, ...]
                }
    """
    results = []
    for entry in RunSetEntry.select().where(RunSetEntry.runset == runset_id).join(
            HyperQuestResultModel).join(PredictorPerformanceResultModel).switch(
                HyperQuestResultModel).join(
                    DataGrabberModel).switch(
                        RunSetEntry).join(RunSet):

        hq = entry.hq_result
        hq_without_joins = HyperQuestResultModel.select().where(
            HyperQuestResultModel.id == hq.id).get()

        hq_fields = get_model_obj_instantiated_fields(hq_without_joins, ignore=[])
        grabber_fields = get_model_obj_instantiated_fields(
            hq.datagrabber_id,
            ignore=['normalization_info'])
        predictor_fields = get_model_obj_instantiated_fields(hq.predictor_perf_result_id)

        results.append({
            'runset': get_model_obj_instantiated_fields(entry.runset, ignore=[]),
            'hq': hq_fields,
            'grabber': grabber_fields,
            'predictor': predictor_fields
            })

    return jsonify(results)


@app.route('/api/get_datagrabber_params/<datagrabber_id>')
def get_datagrabber_params(datagrabber_id):
    """Fetch datagrabber params"""
    grabber = DataGrabberModel.get_from_id(datagrabber_id)
    grabber_fields = get_model_obj_instantiated_fields(
        grabber,
        ignore=['normalization_info'])

    return jsonify(grabber_fields)

@app.route('/api/get_hqresult_params/<hqresult_id>')
def get_hqresult_params(hqresult_id):
    """Fetch datagrabber params"""
    hqr = HyperQuestResultModel.get(HyperQuestResultModel.id == hqresult_id)
    hqr_fields = get_model_obj_instantiated_fields(
        hqr,
        ignore=[])

    return jsonify(hqr_fields)

