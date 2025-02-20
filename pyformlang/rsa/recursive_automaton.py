"""
Representation of a recursive automaton
"""

from typing import AbstractSet

from pyformlang.finite_automaton.finite_automaton import to_symbol
from pyformlang.finite_automaton.symbol import Symbol
from pyformlang.regular_expression import Regex
from pyformlang.cfg import CFG, Epsilon

from pyformlang.rsa.box import Box


def remove_repetition_of_nonterminals_from_productions(grammar_in_text: str):
    """ Remove nonterminal repeats on the left side of the rule
    For example:
    grammar: S -> a S b
             S -> a b
    grammar after function execution: S -> a S b | a b
    """
    productions = dict()
    for production in grammar_in_text.splitlines():
        if "->" not in production:
            continue

        head, body = production.split(" -> ")
        if head in productions:
            productions[head] += " | " + body
        else:
            productions[head] = body

    grammar_new = str()
    for nonterminal in productions:
        grammar_new += f'{nonterminal} -> {productions[nonterminal]}\n'
    return grammar_new[:-1]


class RecursiveAutomaton:
    """ Represents a recursive automaton

    This class represents a recursive automaton.

    Parameters
    ----------
    labels : set of :class:`~pyformlang.finite_automaton.Symbol`, optional
        A finite set of labels for boxes
    initial_label : :class:`~pyformlang.finite_automaton.Symbol`, optional
        A start label for automaton
    boxes : set of :class:`~pyformlang.rsa.Box`, optional
        A finite set of boxes

    """

    def __init__(self,
                 labels: AbstractSet[Symbol] = None,
                 initial_label: Symbol = None,
                 boxes: AbstractSet[Box] = None):

        if labels is not None:
            labels = {to_symbol(x) for x in labels}
        self._labels = labels or set()

        if initial_label is not None:
            initial_label = to_symbol(initial_label)
            if initial_label not in self._labels:
                self._labels.add(initial_label)
        self._initial_label = initial_label or Symbol("")

        self._boxes = dict()
        if boxes is not None:
            for box in boxes:
                self._boxes.update({to_symbol(box.label): box})
                self._labels.add(box.label)

        for label in self._labels:
            box = self.get_box(label)
            if box is None:
                raise ValueError("RSA must have the same number of labels and DFAs")

    def get_box(self, label: Symbol):
        """ Box by label """

        label = to_symbol(label)
        if label in self._boxes:
            return self._boxes[label]

        return None

    def add_box(self, new_box: Box):
        """ Set a box

        Parameters
        -----------
        new_box : :class:`~pyformlang.rsa.Box`
            The new box

        """

        self._boxes.update({new_box.label: new_box})
        self._labels.add(to_symbol(new_box.label))

    def get_number_of_boxes(self):
        """ Size of set of boxes """

        return len(self._boxes)

    def change_initial_label(self, new_initial_label: Symbol):
        """ Set an initial label

        Parameters
        -----------
        new_initial_label : :class:`~pyformlang.finite_automaton.Symbol`
            The new initial label

        """

        new_initial_label = to_symbol(new_initial_label)
        if new_initial_label not in self._labels:
            raise ValueError("New initial label not in set of labels for boxes")

    @property
    def labels(self) -> set:
        """ The set of labels """

        return self._labels

    @property
    def boxes(self) -> dict:
        """ The set of boxes """

        return self._boxes

    @property
    def initial_label(self) -> Symbol:
        """ The initial label """

        return self._initial_label

    @classmethod
    def from_regex(cls, regex: Regex, initial_label: Symbol):
        """ Create a recursive automaton from regular expression

        Parameters
        -----------
        regex : :class:`~pyformlang.regular_expression.Regex`
            The regular expression
        initial_label : :class:`~pyformlang.finite_automaton.Symbol`
            The initial label for the recursive automaton

        Returns
        -----------
        rsa : :class:`~pyformlang.rsa.RecursiveAutomaton`
            The new recursive automaton built from regular expression
        """

        initial_label = to_symbol(initial_label)
        box = Box(regex.to_epsilon_nfa().minimize(), initial_label)
        return RecursiveAutomaton({initial_label}, initial_label, {box})

    @classmethod
    def from_cfg(cls, cfg: CFG):
        """ Create a recursive automaton from context-free grammar

        Parameters
        -----------
        cfg : :class:`~pyformlang.cfg.CFG`
            The context-free grammar

        Returns
        -----------
        rsa : :class:`~pyformlang.rsa.RecursiveAutomaton`
            The new recursive automaton built from context-free grammar
        """

        initial_label = to_symbol(cfg.start_symbol)
        grammar_in_true_format = remove_repetition_of_nonterminals_from_productions(cfg.to_text())

        boxes = set()
        labels = set()
        notation_for_epsilon = Epsilon().to_text()
        for production in grammar_in_true_format.splitlines():
            head, body = production.split(" -> ")
            labels.add(to_symbol(head))

            if body == "":
                body = notation_for_epsilon

            boxes.add(Box(Regex(body).to_epsilon_nfa().minimize(), to_symbol(head)))

        return RecursiveAutomaton(labels, initial_label, boxes)

    def is_equivalent_to(self, other):
        """ Check whether two recursive automata are equivalent

        Parameters
        ----------
        other : :class:`~pyformlang.rsa.RecursiveAutomaton`
            The input recursive automaton

        Returns
        ----------
        are_equivalent : bool
            Whether the two recursive automata are equivalent or not
        """

        if not isinstance(other, RecursiveAutomaton):
            return False

        if self._labels != other._labels:
            return False

        for label in self._labels:
            box_1 = self.get_box(label)
            box_2 = other.get_box(label)

            if not box_1 == box_2:
                return False

        return True

    def __eq__(self, other):
        return self.is_equivalent_to(other)
