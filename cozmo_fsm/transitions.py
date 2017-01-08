import random

from .base import *
from .events import *

class NullTrans(Transition):
    """Transition fires immediately; does not require an event to trigger it."""
    def start(self,event=None):
        if self.running: return
        super().start(event)
        # Don't fire immediately on start because the source node(s) may
        # have other startup calls to make. Give them time to finish.
        self.robot.loop.call_soon(self.fire)


class CSFEventBase(Transition):
    """Base class for Completion, Success, and Failure Events"""
    def __init__(self,event_type,count=None):
        super().__init__()
        self.event_type = event_type
        self.count = count

    def start(self,event=None):
        if self.running: return
        super().start(event)
        self.observed_sources = set()
        for source in self.sources:
            self.robot.erouter.add_listener(self, self.event_type, source)

    def handle_event(self,event):
        if not self.running: return
        if TRACE.trace_level >= TRACE.listener_invocation:
            print('TRACE%d: %s is handling %s' %
                  (TRACE.listener_invocation, self,event))
        super().handle_event(event)
        if isinstance(event, self.event_type):
            self.observed_sources.add(event.source)
            if len(self.observed_sources) >= (self.count or len(self.sources)):
                self.fire(event)
        else:
            raise ValueError("%s can't handle %s" % (self.event_type, event))

class CompletionTrans(CSFEventBase):
    """Transition fires when a source node completes."""
    def __init__(self,count=None):
        super().__init__(CompletionEvent,count)

class SuccessTrans(CSFEventBase):
    """Transition fires when a source node succeeds."""
    def __init__(self,count=None):
        super().__init__(SuccessEvent,count)

class FailureTrans(CSFEventBase):
    """Transition fires when a source node fails."""
    def __init__(self,count=None):
        super().__init__(FailureEvent,count)


class TimerTrans(Transition):
    """Transition fires when the timer has expired."""
    def __init__(self,duration=None):
        if not isinstance(duration, (int, float)) or duration < 0:
            raise ValueError("TimerTrans requires a positive number for duration, not %s" % duration)
        super().__init__()
        self.set_polling_interval(duration)

    def poll(self):
        self.fire()


class TapTrans(Transition):
    """Transition fires when a cube is tapped."""
    def __init__(self,cube=None):
        super().__init__()
        self.cube = cube

    def start(self,event):
        if self.running: return
        super().start(event)
        self.robot.erouter.add_listener(self,TapEvent,self.cube)

    def handle_event(self,event):
        if self.cube:
            self.fire(event)
        else:
            self.handle = \
                self.robot.loop.call_later(Transition.default_value_delay, self.fire, event)

class DataTrans(Transition):
    """Transition fires when data matches."""
    def __init__(self,data=None):
        super().__init__()
        self.data = data

    def start(self,event=None):
        if self.running: return
        super().start(event)
        for source in self.sources:
            self.robot.erouter.add_listener(self, DataEvent, source)

    def handle_event(self,event):
        super().handle_event(event)
        if isinstance(event,DataEvent):
            if self.data is None or self.data == event.data: 
                self.fire(event)
        else:
            raise TypeError('%s is not a DataEvent' % event)

class TextMsgTrans(Transition):
    """Transition fires when message matches."""
    def __init__(self,message=None):
        super().__init__()
        self.source = message

    def start(self,event=None):
        if self.running: return
        super().start(event)
        # The 'source' is the message text.
        self.robot.erouter.add_listener(self, TextMsgEvent, self.source)

    def handle_event(self,event):
        super().handle_event(event)
        if isinstance(event,TextMsgEvent): # erouter checked for match
            self.fire(event)
        else:
            raise TypeError('%s is not a TextMsgEvent' % event)

class RandomTrans(Transition):
    """Picks a destination node at random."""
    def start(self,event=None):
        if self.running: return
        super().start(event)
        # Don't fire immediately on start because the source node(s) may
        # have other startup calls to make. Give them time to finish.
        self.robot.loop.call_soon(self.fire)  # okay to use Transition.fire

    def fire2(self,event):
        """Overrides Transition.fire2 to only start one randomly-chosen destination node."""
        dest = random.choice(self.destinations)
        dest.start(event)
