"""
### BEGIN NODE INFO
[info]
name = update
version = 1.1
description = Fixed update server with proper client management
instancename = update

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""
from labrad.server import setting, LabradServer
from labrad.server import Signal
from twisted.internet.defer import inlineCallbacks


class UpdateServer(LabradServer):
    name = 'update'
    signal = Signal(1, 'signal: signal', 's')

    def initServer(self):
        """Initialize server state"""
        self.updates = {}  # {channel_name: set(client_IDs)}
        self.client_channels = {}  # {client_ID: set(channel_names)}

    @setting(10, name='s', returns='')
    def register(self, c, name):
        """Register a client to listen to updates on a named channel"""
        if name not in self.updates:
            self.updates[name] = set()

        # Add client to channel
        self.updates[name].add(c.ID)

        # Track channels per client for cleanup
        if c.ID not in self.client_channels:
            self.client_channels[c.ID] = set()
        self.client_channels[c.ID].add(name)

        print("Client {} registered for updates on '{}'".format(c.ID, name))

    @setting(11, name='s', returns='')
    def remove(self, c, name):
        """Remove a client from a named channel"""
        if name in self.updates and c.ID in self.updates[name]:
            self.updates[name].remove(c.ID)

            # Clean up empty channels
            if not self.updates[name]:
                del self.updates[name]

        if c.ID in self.client_channels and name in self.client_channels[c.ID]:
            self.client_channels[c.ID].remove(name)

            # Clean up empty client records
            if not self.client_channels[c.ID]:
                del self.client_channels[c.ID]

        print("Client {} removed from updates on '{}'".format(c.ID, name))

    @setting(12, name='s', update='s', returns='')
    def emit(self, c, name, update):
        """Emit an update to all registered listeners on a channel"""
        if name not in self.updates:
            # Auto-create channel if it doesn't exist
            print("Warning: Channel '{}' doesn't exist, creating it".format(name))
            self.updates[name] = set()
            return

        listeners = self.updates[name].copy()

        # Remove the emitter from listeners (they don't need to hear their own message)
        listeners.discard(c.ID)

        if listeners:
            self.signal(update, list(listeners))
            print("Update sent to {} listeners on '{}': {}...".format(len(listeners), name, update[:100]))
        else:
            print("No listeners for channel '{}'".format(name))

    @setting(13, returns='*s')
    def list_channels(self, c):
        """List all active channels"""
        return list(self.updates.keys())

    @setting(14, name='s', returns='*s')
    def list_listeners(self, c, name):
        """List client IDs listening to a specific channel"""
        if name in self.updates:
            return [str(client_id) for client_id in self.updates[name]]
        return []

    @setting(15, returns='s')
    def get_status(self, c):
        """Get server status information"""
        total_channels = len(self.updates)
        total_listeners = sum(len(listeners) for listeners in self.updates.values())
        return "Channels: {}, Total listeners: {}".format(total_channels, total_listeners)

    def clientDisconnected(self, c):
        """Clean up when a client disconnects"""
        client_id = c.ID

        if client_id in self.client_channels:
            # Remove client from all channels they were registered to
            channels = self.client_channels[client_id].copy()
            for channel in channels:
                if channel in self.updates:
                    self.updates[channel].discard(client_id)
                    # Clean up empty channels
                    if not self.updates[channel]:
                        del self.updates[channel]

            # Remove client record
            del self.client_channels[client_id]

            print("Cleaned up disconnected client {} from {} channels".format(client_id, len(channels)))


Server = UpdateServer

if __name__ == "__main__":
    from labrad import util
    util.runServer(Server())
