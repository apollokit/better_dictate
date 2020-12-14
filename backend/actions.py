"""module for dealing with actions taken by the app
"""
from typing import List

class Action:
    """An action that can be taken by the app

    For now, includes:
    - written text
    - executed commands
    """
    def undo(self) -> bool:
        """Reverts the effect of the action

        Should be implemented in action subclasses

        Basically, if the user would expect an undo for this action to 
        actually count as an undo, then it's substantial. The primary use 
        case for this is for the undo action itself (UndoUtteranceCmdExec).
        Technically, undo can be "undone", because it's added to the action
        history, but it's a noop, and when that's the last thing on the
        history, it really doesn't count.

        Returns:
            True if this undo was "substantial".  
        """
        raise NotImplementedError

class UtteranceHistory:
    """History of the actions in one utterance
    """
    def __init__(self, actions: List[Action]):
        """Init
        
        Args:
            actions: the actions taken during the utterance, in temporal order
        """
        self.actions = actions

    def undo(self) -> bool:
        """Undo the utterance

        Returns:
            True if this undo was "substantial". See documentation for     
                Action() for more information
        """
        substantial = False
        for action in reversed(self.actions):
            # if any of the actions was considered substantial, the whole utterance is substantial
            new_substantial = action.undo()
            substantial = substantial or new_substantial
        return substantial


class ActionHistory:
    """Maintains a history of actions that have been taken over the
    course of multiple occurrences    
    """
    def __init__(self):
        self.utterance_history: List[UtteranceHistory] = []

    def add_utterance_actions(self, actions: List[Action]):
        """Add a new utterance from the actions in that utterance
        
        Args:
            actions: the actions for the utterance
        """
        utterance = UtteranceHistory(actions)
        self.utterance_history.append(utterance)

    def undo_utterance(self) -> bool:
        """Undo the last utterance

        Returns:
            True if this undo was "substantial". See documentation for     
                Action() for more information
        """
        last_utterance = self.utterance_history.pop()
        return last_utterance.undo()


