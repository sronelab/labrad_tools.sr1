import json
import labrad
from twisted.internet.defer import inlineCallbacks


class UpdateProxy(object):
    """
    Improved proxy for the update server with better error handling
    and connection management.
    """

    def __init__(self, channel_name):
        """
        Initialize the proxy for a specific channel.

        Args:
            channel_name (str): Name of the update channel to emit to
        """
        self.channel_name = channel_name
        self._cxn = None
        self._server = None
        self._connect()

    def _connect(self):
        """Establish connection to the update server"""
        try:
            self._cxn = labrad.connect()
            self._server = self._cxn.update
            print("UpdateProxy connected to update server for channel '{}'".format(self.channel_name))
        except Exception as e:
            print("UpdateProxy failed to connect: {}".format(e))
            self._cxn = None
            self._server = None

    def emit(self, message_data):
        """
        Emit an update message to the channel.

        Args:
            message_data: Data to send (will be JSON serialized)
        """
        if self._server is None:
            print("UpdateProxy not connected, attempting to reconnect...")
            self._connect()
            if self._server is None:
                print("UpdateProxy emit failed: no connection")
                return False

        try:
            if isinstance(message_data, (dict, list)):
                message_json = json.dumps(message_data)
            else:
                message_json = str(message_data)

            self._server.emit(self.channel_name, message_json)
            return True

        except Exception as e:
            print("UpdateProxy emit failed: {}".format(e))
            # Try to reconnect for next time
            self._connect()
            return False

    def close(self):
        """Close the connection"""
        if self._cxn is not None:
            try:
                self._cxn.disconnect()
            except:
                pass
            self._cxn = None
            self._server = None


class UpdateListener(object):
    """
    Helper class for listening to update server channels.
    """

    def __init__(self, channel_name, callback_function):
        """
        Initialize listener for a channel.

        Args:
            channel_name (str): Channel to listen to
            callback_function: Function to call when updates received
        """
        self.channel_name = channel_name
        self.callback = callback_function
        self._cxn = None
        self._server = None
        self._signal_id = None

    @inlineCallbacks
    def connect_and_listen(self):
        """Connect to update server and start listening"""
        try:
            # Connect to LabRAD
            self._cxn = yield labrad.connect()
            self._server = yield self._cxn.update

            # Register for updates
            yield self._server.register(self.channel_name)

            # Setup signal listener
            self._signal_id = hash(self.channel_name) % 100000  # Generate unique ID
            yield self._server.signal__signal.connect(self._signal_id)
            yield self._server.addListener(
                listener=self._on_signal,
                source=None,
                ID=self._signal_id
            )

            print("UpdateListener connected to channel '{}'".format(self.channel_name))

        except Exception as e:
            print("UpdateListener connection failed: {}".format(e))
            raise

    def _on_signal(self, context, data):
        """Handle incoming signals"""
        try:
            # Try to parse as JSON
            try:
                parsed_data = json.loads(data)
            except json.JSONDecodeError:
                parsed_data = data

            # Call the user's callback
            self.callback(parsed_data)

        except Exception as e:
            print("UpdateListener callback error: {}".format(e))

    @inlineCallbacks
    def disconnect(self):
        """Disconnect from the server"""
        if self._server is not None:
            try:
                yield self._server.remove(self.channel_name)
            except:
                pass

        if self._cxn is not None:
            try:
                yield self._cxn.disconnect()
            except:
                pass

        self._cxn = None
        self._server = None
