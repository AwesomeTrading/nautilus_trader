# -------------------------------------------------------------------------------------------------
# <copyright file="order.pyx" company="Nautech Systems Pty Ltd">
#  Copyright (C) 2015-2019 Nautech Systems Pty Ltd. All rights reserved.
#  The use of this source code is governed by the license as found in the LICENSE.md file.
#  https://nautechsystems.io
# </copyright>
# -------------------------------------------------------------------------------------------------

import uuid

from cpython.datetime cimport datetime
from decimal import Decimal
from typing import List

from nautilus_trader.core.correctness cimport Condition
from nautilus_trader.core.types cimport GUID
from nautilus_trader.model.c_enums.order_side cimport OrderSide, order_side_to_string
from nautilus_trader.model.c_enums.order_type cimport OrderType, order_type_to_string
from nautilus_trader.model.c_enums.order_status cimport OrderStatus, order_status_to_string
from nautilus_trader.model.c_enums.time_in_force cimport TimeInForce, time_in_force_to_string
from nautilus_trader.model.objects cimport Quantity, Symbol, Price
from nautilus_trader.model.events cimport (
    OrderEvent,
    OrderFillEvent,
    OrderInitialized,
    OrderSubmitted,
    OrderAccepted,
    OrderRejected,
    OrderWorking,
    OrderExpired,
    OrderModified,
    OrderCancelled,
    OrderCancelReject)
from nautilus_trader.model.identifiers cimport Label, IdTag, OrderId, ExecutionId, ExecutionTicket
from nautilus_trader.model.generators cimport OrderIdGenerator
from nautilus_trader.common.clock cimport Clock, LiveClock


# Order types which require a price to be valid
cdef set PRICED_ORDER_TYPES = {
    OrderType.LIMIT,
    OrderType.STOP_MARKET,
    OrderType.STOP_LIMIT,
    OrderType.MIT}


cdef class Order:
    """
    Represents an order for a financial market instrument.
    """

    def __init__(self,
                 OrderId order_id,
                 Symbol symbol,
                 OrderSide order_side,
                 OrderType order_type,  # 'type' hides keyword
                 Quantity quantity,
                 datetime timestamp,
                 Price price=None,
                 Label label=None,
                 TimeInForce time_in_force=TimeInForce.DAY,
                 datetime expire_time=None,
                 GUID init_id=None):
        """
        Initializes a new instance of the Order class.

        :param order_id: The order_id.
        :param symbol: The order symbol.
        :param order_side: The order side.
        :param order_type: The order type.
        :param quantity: The order quantity (> 0).
        :param timestamp: The order initialization timestamp.
        :param price: The order price (must be None for non-priced orders).
        :param label: The order label / secondary identifier (optional can be None).
        :param time_in_force: The order time in force (default DAY).
        :param expire_time: The order expire time (optional can be None).
        :param init_id: The order initialization event identifier.
        :raises ConditionFailed: If the order quantity is not positive (> 0).
        :raises ConditionFailed: If the order side is UNKNOWN.
        :raises ConditionFailed: If the order type should not have a price and the price is not None.
        :raises ConditionFailed: If the order type should have a price and the price is None.
        :raises ConditionFailed: If the time_in_force is GTD and the expire_time is None.
        """
        Condition.positive(quantity.value, 'quantity')
        Condition.true(order_side != OrderSide.UNKNOWN, 'order_side != UNKNOWN')

        # For orders which require a price
        if order_type in PRICED_ORDER_TYPES:
            Condition.not_none(price, 'price')
        # For orders which require no price
        else:
            Condition.none(price, 'price')

        if time_in_force == TimeInForce.GTD:
            Condition.not_none(expire_time, 'expire_time')

        self._order_ids_broker = []         # type: List[OrderId]
        self._execution_ids = []            # type: List[ExecutionId]
        self._execution_tickets = []        # type: List[ExecutionTicket]
        self._events = []                   # type: List[OrderEvent]

        self.id = order_id
        self.id_broker = None               # Can be None
        self.account_id = None              # Can be None
        self.execution_id = None            # Can be None
        self.execution_ticket = None        # Can be None
        self.symbol = symbol
        self.side = order_side
        self.type = order_type
        self.quantity = quantity
        self.timestamp = timestamp
        self.price = price                  # Can be None
        self.label = label                  # Can be None
        self.time_in_force = time_in_force  # Can be None
        self.expire_time = expire_time      # Can be None
        self.filled_quantity = Quantity(0)
        self.filled_timestamp = None        # Can be None
        self.average_price = None           # Can be None
        self.slippage = Decimal(0.0)
        self.status = OrderStatus.INITIALIZED
        self.init_id = GUID(uuid.uuid4()) if init_id is None else init_id
        self.is_buy = self.side == OrderSide.BUY
        self.is_sell = self.side == OrderSide.SELL
        self.is_working = False
        self.is_completed = False

        cdef OrderInitialized initialized = OrderInitialized(
            order_id=order_id,
            symbol=symbol,
            label=label,
            order_side=order_side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            time_in_force=time_in_force,
            expire_time=expire_time,
            event_id=self.init_id,
            event_timestamp=timestamp)

        # Update events
        self._events.append(initialized)
        self.last_event = initialized

    @staticmethod
    cdef Order create(OrderInitialized event):
        """
        Return an order from the given initialized event.
        
        :param event: The event to initialize with.
        :return Order.
        """
        return Order(
            order_id=event.order_id,
            symbol=event.symbol,
            order_side=event.order_side,
            order_type=event.order_type,
            quantity=event.quantity,
            timestamp=event.timestamp,
            price=event.price,
            label=event.label,
            time_in_force=event.time_in_force,
            expire_time=event.expire_time,
            init_id=event.id)

    cdef bint equals(self, Order other):
        """
        Return a value indicating whether this object is equal to the given object.

        :param other: The other object.
        :return bool.
        """
        return self.id.equals(other.id)

    def __eq__(self, Order other) -> bool:
        """
        Return a value indicating whether this object is equal to the given object.

        :param other: The other object.
        :return bool.
        """
        return self.equals(other)

    def __ne__(self, Order other) -> bool:
        """
        Return a value indicating whether this object is not equal to the given object.

        :param other: The other object.
        :return bool.
        """
        return not self.equals(other)

    def __hash__(self) -> int:
        """"
        Return a hash representation of this object.

        :return int.
        """
        return hash(self.id)

    def __str__(self) -> str:
        """
        Return a string representation of this object.

        :return str.
        """
        cdef str quantity = '{:,}'.format(self.quantity.value)
        cdef str label = '' if self.label is None else f', label={self.label.value}'
        cdef str price = '' if self.price is None else f'@ {self.price} '
        cdef str expire_time = '' if self.expire_time is None else f' {self.expire_time}'
        return (f"Order({self.id.value}{label}, status={order_status_to_string(self.status)}) "
                f"{order_side_to_string(self.side)} {quantity} {self.symbol} {order_type_to_string(self.type)} {price}"
                f"{time_in_force_to_string(self.time_in_force)}{expire_time}")

    def __repr__(self) -> str:
        """
        Return a string representation of this object which includes the objects
        location in memory.

        :return str.
        """
        return f"<{str(self)} object at {id(self)}>"

    cpdef str status_as_string(self):
        """
        Return the order status as a string.
        
        :return str.
        """
        return order_status_to_string(self.status)

    cpdef list get_order_ids_broker(self):
        """
        Return a list of broker order_ids.
        
        :return List[OrderId]. 
        """
        return self._order_ids_broker.copy()

    cpdef list get_execution_ids(self):
        """
        Return a list of execution identifiers.
        
        :return List[ExecutionId].
        """
        return self._execution_ids.copy()

    cpdef list get_execution_tickets(self):
        """
        Return a list of execution tickets.
        
        :return List[ExecutionTicket]. 
        """
        return self._execution_tickets.copy()

    cpdef list get_events(self):
        """
        Return a list or order events.
        
        :return List[OrderEvent]. 
        """
        return self._events.copy()

    cpdef int event_count(self):
        """
        Return the count of events applied to the order.
        
        :return int.
        """
        return len(self._events)

    cpdef void apply(self, OrderEvent event):
        """
        Apply the given order event to the order.

        :param event: The order event to apply.
        :raises ConditionFailed: If the order_events order_id is not equal to the order_id.
        :raises ConditionFailed: If the order account_id is not None and the order_events account_id is not equal to the order account_id.
        """
        Condition.equal(self.id, event.order_id)
        if self.account_id is not None:
            Condition.equal(self.account_id, event.account_id)

        # Update events
        self._events.append(event)
        self.last_event = event

        # Handle event
        if isinstance(event, OrderSubmitted):
            self.status = OrderStatus.SUBMITTED
            self.account_id = event.account_id
        elif isinstance(event, OrderRejected):
            self.status = OrderStatus.REJECTED
            self.is_completed = True
        elif isinstance(event, OrderAccepted):
            self.status = OrderStatus.ACCEPTED
        elif isinstance(event, OrderWorking):
            self.status = OrderStatus.WORKING
            self._order_ids_broker.append(event.order_id_broker)
            self.id_broker = event.order_id_broker
            self.is_working = True
        elif isinstance(event, OrderCancelReject):
            pass
        elif isinstance(event, OrderCancelled):
            self.status = OrderStatus.CANCELLED
            self.is_working = False
            self.is_completed = True
        elif isinstance(event, OrderExpired):
            self.status = OrderStatus.EXPIRED
            self.is_working = False
            self.is_completed = True
        elif isinstance(event, OrderModified):
            self._order_ids_broker.append(event.order_id_broker)
            self.id_broker = event.order_id_broker
            self.price = event.modified_price
        elif isinstance(event, OrderFillEvent):
            self._execution_ids.append(event.execution_id)
            self._execution_tickets.append(event.execution_ticket)
            self.execution_id = event.execution_id
            self.execution_ticket = event.execution_ticket
            self.filled_quantity = event.filled_quantity
            self.filled_timestamp = event.timestamp
            self.average_price = event.average_price
            self._set_slippage()
            self._set_fill_status()
            if self.status == OrderStatus.FILLED:
                self.is_working = False
                self.is_completed = True

    cdef void _set_slippage(self):
        if self.type not in PRICED_ORDER_TYPES:
            # Slippage only applicable to priced order types
            return

        if self.side == OrderSide.BUY:
            self.slippage = self.average_price - self.price
        else:  # self.side == OrderSide.SELL:
            self.slippage = self.price - self.average_price

        # Avoids negative zero (-0.00000)
        if self.slippage == 0:
            self.slippage = Decimal(0)

    cdef void _set_fill_status(self):
        if self.filled_quantity < self.quantity:
            self.status = OrderStatus.PARTIALLY_FILLED
        elif self.filled_quantity == self.quantity:
            self.status = OrderStatus.FILLED
        elif self.filled_quantity > self.quantity:
            self.status = OrderStatus.OVER_FILLED


cdef class AtomicOrder:
    """
    Represents an order for a financial market instrument consisting of a 'parent'
    entry order and 'child' OCO orders representing a stop-loss and optional
    profit target.
    """
    def __init__(self,
                 Order entry,
                 Order stop_loss,
                 Order take_profit=None):
        """
        Initializes a new instance of the AtomicOrder class.

        :param entry: The entry 'parent' order.
        :param stop_loss: The stop-loss (S/L) 'child' order.
        :param take_profit: The take-profit (T/P) 'child' order (optional can be None).
        """
        self.id = OrderId('A' + entry.id.value)
        self.entry = entry
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.has_take_profit = take_profit is not None
        self.timestamp = entry.timestamp

    cdef bint equals(self, AtomicOrder other):
        """
        Return a value indicating whether this object is equal to the given object.

        :param other: The other object.
        :return bool.
        """
        return self.id.equals(other.id)

    def __eq__(self, AtomicOrder other) -> bool:
        """
        Return a value indicating whether this object is equal to the given object.

        :param other: The other object.
        :return bool.
        """
        return self.equals(other)

    def __ne__(self, AtomicOrder other) -> bool:
        """
        Return a value indicating whether this object is not equal to the given object.

        :param other: The other object.
        :return bool.
        """
        return not self.equals(other)

    def __hash__(self) -> int:
        """"
        Return a hash representation of this object.

        :return int.
        """
        return hash(self.id)

    def __str__(self) -> str:
        """
        Return a string representation of this object.

        :return str.

        :return str.
        """
        cdef str take_profit = 'NONE' if self.take_profit is None else str(self.take_profit)
        return f"AtomicOrder({self.id.value}, Entry{self.entry}, SL={self.stop_loss}, TP={take_profit})"

    def __repr__(self) -> str:
        """
        Return a string representation of this object which includes the objects
        location in memory.

        :return str.
        """
        return f"<{str(self)} object at {id(self)}>"


cdef class OrderFactory:
    """
    A factory class which provides different order types.
    """

    def __init__(self,
                 IdTag id_tag_trader,
                 IdTag id_tag_strategy,
                 Clock clock=LiveClock()):
        """
        Initializes a new instance of the OrderFactory class.

        :param id_tag_trader: The identifier tag for the trader.
        :param id_tag_strategy: The identifier tag for the strategy.
        :param clock: The clock for the component.
        """
        self._clock = clock
        self._id_generator = OrderIdGenerator(
            id_tag_trader=id_tag_trader,
            id_tag_strategy=id_tag_strategy,
            clock=clock)

    cpdef void reset(self):
        """
        Reset the order factory by clearing all stateful values.
        """
        self._id_generator.reset()

    cpdef Order market(
            self,
            Symbol symbol,
            OrderSide order_side,
            Quantity quantity,
            Label label=None):
        """
        Return a market order with the given parameters.

        :param symbol: The orders symbol.
        :param order_side: The orders side.
        :param quantity: The orders quantity (> 0).
        :param label: The orders label (optional can be None).
        :raises ConditionFailed: If the order quantity is not positive (> 0).
        :return Order.
        """
        return Order(
            self._id_generator.generate(),
            symbol,
            order_side,
            OrderType.MARKET,
            quantity,
            self._clock.time_now(),
            price=None,
            label=label,
            time_in_force=TimeInForce.DAY,
            expire_time=None)

    cpdef Order limit(
            self,
            Symbol symbol,
            OrderSide order_side,
            Quantity quantity,
            Price price,
            Label label=None,
            TimeInForce time_in_force=TimeInForce.DAY,
            datetime expire_time=None):
        """
        Returns a limit order with the given parameters.

        Note: If the time in force is GTD then a valid expire time must be given.
        :param symbol: The orders symbol.
        :param order_side: The orders side.
        :param quantity: The orders quantity (> 0).
        :param price: The orders price.
        :param label: The orders label (optional can be None).
        :param time_in_force: The orders time in force (optional can be None).
        :param expire_time: The orders expire time (optional can be None - unless time_in_force is GTD).
        :return Order.
        :raises ConditionFailed: If the order quantity is not positive (> 0).
        :raises ConditionFailed: If the time_in_force is GTD and the expire_time is None.
        """
        return Order(
            self._id_generator.generate(),
            symbol,
            order_side,
            OrderType.LIMIT,
            quantity,
            self._clock.time_now(),
            price,
            label,
            time_in_force,
            expire_time)

    cpdef Order stop_market(
            self,
            Symbol symbol,
            OrderSide order_side,
            Quantity quantity,
            Price price,
            Label label=None,
            TimeInForce time_in_force=TimeInForce.DAY,
            datetime expire_time=None):
        """
        Returns a stop-market order with the given parameters.

        Note: If the time in force is GTD then a valid expire time must be given.
        :param symbol: The orders symbol.
        :param order_side: The orders side.
        :param quantity: The orders quantity (> 0).
        :param price: The orders price.
        :param label: The orders label (optional can be None).
        :param time_in_force: The orders time in force (optional can be None).
        :param expire_time: The orders expire time (optional can be None - unless time_in_force is GTD).
        :return Order.
        :raises ConditionFailed: If the order quantity is not positive (> 0).
        :raises ConditionFailed: If the time_in_force is GTD and the expire_time is None.
        """
        return Order(
            self._id_generator.generate(),
            symbol,
            order_side,
            OrderType.STOP_MARKET,
            quantity,
            self._clock.time_now(),
            price,
            label,
            time_in_force,
            expire_time)

    cpdef Order stop_limit(
            self,
            Symbol symbol,
            OrderSide order_side,
            Quantity quantity,
            Price price,
            Label label=None,
            TimeInForce time_in_force=TimeInForce.DAY,
            datetime expire_time=None):
        """
        Return a stop-limit order with the given parameters.

        Note: If the time in force is GTD then a valid expire time must be given.
        :param symbol: The orders symbol.
        :param order_side: The orders side.
        :param quantity: The orders quantity (> 0).
        :param price: The orders price.
        :param label: The orders label (optional can be None).
        :param time_in_force: The orders time in force (optional can be None).
        :param expire_time: The orders expire time (optional can be None - unless time_in_force is GTD).
        :return Order.
        :raises ConditionFailed: If the order quantity is not positive (> 0).
        :raises ConditionFailed: If the time_in_force is GTD and the expire_time is None.
        """
        return Order(
            self._id_generator.generate(),
            symbol,
            order_side,
            OrderType.STOP_LIMIT,
            quantity,
            self._clock.time_now(),
            price,
            label,
            time_in_force,
            expire_time)

    cpdef Order market_if_touched(
            self,
            Symbol symbol,
            OrderSide order_side,
            Quantity quantity,
            Price price,
            Label label=None,
            TimeInForce time_in_force=TimeInForce.DAY,
            datetime expire_time=None):
        """
        Return a market-if-touched order with the given parameters.
        
        Note: If the time in force is GTD then a valid expire time must be given.
        :param symbol: The orders symbol.
        :param order_side: The orders side.
        :param quantity: The orders quantity (> 0).
        :param price: The orders price.
        :param label: The orders label (optional can be None).
        :param time_in_force: The orders time in force (optional can be None).
        :param expire_time: The orders expire time (optional can be None - unless time_in_force is GTD).
        :return Order.
        :raises ConditionFailed: If the order quantity is not positive (> 0).
        :raises ConditionFailed: If the time_in_force is GTD and the expire_time is None.
        """
        return Order(
            self._id_generator.generate(),
            symbol,
            order_side,
            OrderType.MIT,
            quantity,
            self._clock.time_now(),
            price,
            label,
            time_in_force,
            expire_time)

    cpdef Order fill_or_kill(
            self,
            Symbol symbol,
            OrderSide order_side,
            Quantity quantity,
            Label label=None):
        """
        Return a fill-or-kill order with the given parameters.

        :param symbol: The orders symbol.
        :param order_side: The orders side.
        :param quantity: The orders quantity (> 0).
        :param label: The orders label (optional can be None).
        :return Order.
        :raises ConditionFailed: If the order quantity is not positive (> 0).
        """
        return Order(
            self._id_generator.generate(),
            symbol,
            order_side,
            OrderType.MARKET,
            quantity,
            self._clock.time_now(),
            price=None,
            label=label,
            time_in_force=TimeInForce.FOC,
            expire_time=None)

    cpdef Order immediate_or_cancel(
            self,
            Symbol symbol,
            OrderSide order_side,
            Quantity quantity,
            Label label=None):
        """
        Return a immediate-or-cancel order with the given parameters.

        :param symbol: The orders symbol.
        :param order_side: The orders side.
        :param quantity: The orders quantity (> 0).
        :param label: The orders label (optional can be None).
        :return Order.
        :raises ConditionFailed: If the order quantity is not positive (> 0).
        """
        return Order(
            self._id_generator.generate(),
            symbol,
            order_side,
            OrderType.MARKET,
            quantity,
            self._clock.time_now(),
            price=None,
            label=label,
            time_in_force=TimeInForce.IOC,
            expire_time=None)

    cpdef AtomicOrder atomic_market(
            self,
            Symbol symbol,
            OrderSide order_side,
            Quantity quantity,
            Price price_stop_loss,
            Price price_take_profit=None,
            Label label=None):
        """
        Return a market entry atomic order with the given parameters.

        :param symbol: The orders symbol.
        :param order_side: The orders side.
        :param quantity: The orders quantity (> 0).
        :param price_stop_loss: The stop-loss order price.
        :param price_take_profit: The take-profit order price (optional can be None).
        :param label: The orders label (optional can be None).
        :return AtomicOrder.
        :raises ConditionFailed: If the order quantity is not positive (> 0).
        """
        cdef Label entry_label = None
        if label is not None:
            entry_label = Label(label.value + '_E')

        cdef Order entry_order = self.market(
            symbol,
            order_side,
            quantity,
            entry_label)

        return self._create_atomic_order(
            entry_order,
            price_stop_loss,
            price_take_profit,
            label)

    cpdef AtomicOrder atomic_limit(
            self,
            Symbol symbol,
            OrderSide order_side,
            Quantity quantity,
            Price price_entry,
            Price price_stop_loss,
            Price price_take_profit=None,
            Label label=None,
            TimeInForce time_in_force=TimeInForce.DAY,
            datetime expire_time=None):
        """
        Return a limit entry atomic order with the given parameters.


        :param symbol: The orders symbol.
        :param order_side: The orders side.
        :param quantity: The orders quantity (> 0).
        :param price_entry: The parent orders entry price.
        :param price_stop_loss: The stop-loss order price.
        :param price_take_profit: The take-profit order price (optional can be None).
        :param label: The order label (optional can be None).
        :param time_in_force: The order time in force (optional can be None).
        :param expire_time: The orders expire time (optional can be None - unless time_in_force is GTD).
        :return AtomicOrder.
        :raises ConditionFailed: If the order quantity is not positive (> 0).
        :raises ConditionFailed: If the time_in_force is GTD and the expire_time is None.
        """
        cdef Label entry_label = None
        if label is not None:
            entry_label = Label(label.value + '_E')

        cdef Order entry_order = self.limit(
            symbol,
            order_side,
            quantity,
            price_entry,
            label,
            time_in_force,
            expire_time)

        return self._create_atomic_order(
            entry_order,
            price_stop_loss,
            price_take_profit,
            label)

    cpdef AtomicOrder atomic_stop_market(
            self,
            Symbol symbol,
            OrderSide order_side,
            Quantity quantity,
            Price price_entry,
            Price price_stop_loss,
            Price price_take_profit=None,
            Label label=None,
            TimeInForce time_in_force=TimeInForce.DAY,
            datetime expire_time=None):
        """
        Return a stop-market entry atomic order with the given parameters.

        :param symbol: The orders symbol.
        :param order_side: The orders side.
        :param quantity: The orders quantity (> 0).
        :param price_entry: The parent orders entry price.
        :param price_stop_loss: The stop-loss order price.
        :param price_take_profit: The take-profit order price (optional can be None).
        :param label: The orders label (optional can be None).
        :param time_in_force: The orders time in force (optional can be None).
        :param expire_time: The orders expire time (optional can be None - unless time_in_force is GTD).
        :return AtomicOrder.
        :raises ConditionFailed: If the order quantity is not positive (> 0).
        :raises ConditionFailed: If the time_in_force is GTD and the expire_time is None.
        """
        cdef Label entry_label = None
        if label is not None:
            entry_label = Label(label.value + '_E')

        cdef Order entry_order = self.stop_market(
            symbol,
            order_side,
            quantity,
            price_entry,
            label,
            time_in_force,
            expire_time)

        return self._create_atomic_order(
            entry_order,
            price_stop_loss,
            price_take_profit,
            label)

    cdef AtomicOrder _create_atomic_order(
        self,
        Order entry,
        Price price_stop_loss,
        Price price_take_profit,
        Label original_label):
        cdef OrderSide child_order_side = OrderSide.BUY if entry.side == OrderSide.SELL else OrderSide.SELL

        cdef Label label_stop_loss = None
        cdef Label label_take_profit = None
        if original_label is not None:
            label_stop_loss = Label(original_label.value + "_SL")
            label_take_profit = Label(original_label.value + "_TP")

        cdef Order stop_loss = self.stop_market(
            entry.symbol,
            child_order_side,
            entry.quantity,
            price_stop_loss,
            label_stop_loss,
            TimeInForce.GTC,
            expire_time=None)

        cdef Order take_profit = None
        if price_take_profit is not None:
            take_profit = self.limit(
                entry.symbol,
                child_order_side,
                entry.quantity,
                price_take_profit,
                label_take_profit,
                TimeInForce.GTC,
                expire_time=None)

        return AtomicOrder(
            entry,
            stop_loss,
            take_profit)
