#!/usr/bin/env python3
# -------------------------------------------------------------------------------------------------
# <copyright file="commands.pyx" company="Invariance Pte">
#  Copyright (C) 2018-2019 Invariance Pte. All rights reserved.
#  The use of this source code is governed by the license as found in the LICENSE.md file.
#  http://www.invariance.com
# </copyright>
# -------------------------------------------------------------------------------------------------

# cython: language_level=3, boundscheck=False, wraparound=False, nonecheck=False

from cpython.datetime cimport datetime

from inv_trader.model.objects cimport ValidString, Price
from inv_trader.model.identifiers cimport GUID, PositionId, TraderId, StrategyId
from inv_trader.model.order cimport Order, AtomicOrder


cdef class Command:
    """
    The base class for all commands.
    """

    def __init__(self, GUID identifier, datetime timestamp):
        """
        Initializes a new instance of the Command abstract class.

        :param identifier: The commands identifier.
        :param timestamp: The commands timestamp.
        """
        self.id = identifier
        self.timestamp = timestamp

    def __eq__(self, Command other) -> bool:
        """
        Override the default equality comparison.
        """
        if isinstance(other, self.__class__):
            return self.id == other.id
        else:
            return False

    def __ne__(self, Command other):
        """
        Override the default not-equals comparison.
        """
        return not self.__eq__(other)

    def __hash__(self) -> int:
        """"
        Override the default hash implementation.
        """
        return hash(self.id)

    def __str__(self) -> str:
        """
        :return: The str() string representation of the command.
        """
        return f"{self.__class__.__name__}()"

    def __repr__(self) -> str:
        """
        :return: The repr() string representation of the command.
        """
        return f"<{str(self)} object at {id(self)}>"


cdef class CollateralInquiry(Command):
    """
    Represents a request for a FIX collateral inquiry of all connected accounts.
    """

    def __init__(self, GUID command_id, datetime command_timestamp):
        """
        Initializes a new instance of the CollateralInquiry class.

        :param command_id: The commands identifier.
        :param command_timestamp: The order commands timestamp.
        """
        super().__init__(command_id, command_timestamp)


cdef class SubmitOrder(Command):
    """
    Represents a command to submit the given order.
    """

    def __init__(self,
                 TraderId trader_id,
                 StrategyId strategy_id,
                 PositionId position_id,
                 Order order,
                 GUID command_id,
                 datetime command_timestamp):
        """
        Initializes a new instance of the SubmitOrder class.

        :param trader_id: The trader identifier associated with the order.
        :param strategy_id: The strategy identifier associated with the order.
        :param position_id: The position identifier associated with the order.
        :param order: The commands order to submit.
        :param command_id: The commands identifier.
        :param command_timestamp: The commands timestamp.
        """
        super().__init__(command_id, command_timestamp)
        self.trader_id = trader_id
        self.strategy_id = strategy_id
        self.position_id = position_id
        self.order = order

    def __str__(self) -> str:
        """
        :return: The str() string representation of the command.
        """
        return f"{self.__class__.__name__}({self.order})"

    def __repr__(self) -> str:
        """
        :return: The repr() string representation of the command.
        """
        return f"<{str(self)} object at {id(self)}>"


cdef class SubmitAtomicOrder(Command):
    """
    Represents a command to submit an atomic order consisting of parent and child orders.
    """

    def __init__(self,
                 TraderId trader_id,
                 StrategyId strategy_id,
                 PositionId position_id,
                 AtomicOrder atomic_order,
                 GUID command_id,
                 datetime command_timestamp):
        """
        Initializes a new instance of the SubmitAtomicOrder class.

        :param atomic_order: The commands atomic order to submit.
        :param trader_id: The trader identifier associated with the order.
        :param strategy_id: The strategy identifier to associate with the order.
        :param position_id: The command position identifier.
        :param command_id: The commands identifier.
        :param command_timestamp: The commands timestamp.
        """
        super().__init__(command_id, command_timestamp)
        self.trader_id = trader_id
        self.strategy_id = strategy_id
        self.position_id = position_id
        self.atomic_order = atomic_order

    def __str__(self) -> str:
        """
        :return: The str() string representation of the command.
        """
        return f"{self.__class__.__name__}({self.atomic_order})"

    def __repr__(self) -> str:
        """
        :return: The repr() string representation of the command.
        """
        return f"<{str(self)} object at {id(self)}>"


cdef class ModifyOrder(Command):
    """
    Represents a command to modify an order with the given modified price.
    """

    def __init__(self,
                 TraderId trader_id,
                 StrategyId strategy_id,
                 OrderId order_id,
                 Price modified_price,
                 GUID command_id,
                 datetime command_timestamp):
        """
        Initializes a new instance of the ModifyOrder class.

        :param trader_id: The trader identifier associated with the order.
        :param strategy_id: The strategy identifier associated with the order.
        :param order_id: The commands order identifier.
        :param modified_price: The commands modified price for the order.
        :param command_id: The commands identifier.
        :param command_timestamp: The commands timestamp.
        """
        super().__init__(command_id, command_timestamp)
        self.trader_id = trader_id
        self.strategy_id = strategy_id
        self.order_id = order_id
        self.modified_price = modified_price


cdef class CancelOrder(Command):
    """
    Represents a command to cancel an order.
    """

    def __init__(self,
                 TraderId trader_id,
                 StrategyId strategy_id,
                 OrderId order_id,
                 ValidString cancel_reason,
                 GUID command_id,
                 datetime command_timestamp):
        """
        Initializes a new instance of the CancelOrder class.

        :param trader_id: The trader identifier associated with the order.
        :param strategy_id: The strategy identifier associated with the order.
        :param order_id: The commands order identifier.
        :param cancel_reason: The reason for cancellation.
        :param command_id: The commands identifier.
        :param command_timestamp: The commands timestamp.
        """
        super().__init__(command_id, command_timestamp)
        self.trader_id = trader_id
        self.strategy_id = strategy_id
        self.order_id = order_id
        self.cancel_reason = cancel_reason
