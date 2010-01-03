from twisted.internet.error import ConnectionDone

from landscape.lib.amp import MethodCall, MethodCallError
from landscape.broker.amp import (
    BrokerServerProtocol, BrokerServerProtocolFactory)
from landscape.tests.helpers import LandscapeTest, DEFAULT_ACCEPTED_TYPES
from landscape.broker.tests.helpers import (
    RemoteBrokerHelper, BrokerClientHelper)


class BrokerServerProtocolFactoryTest(LandscapeTest):

    def test_provides_protocol_type(self):
        """
        The L{BrokerServerProtocolFactory} instantiates protocols objects of
        type L{BrokerServerProtocol}.
        """
        self.assertEquals(BrokerServerProtocolFactory.protocol,
                          BrokerServerProtocol)

    def test_provides_broker_object(self):
        """
        Instances of the L{BrokerServerProtocolFactory} class have a C{broker}
        attribute references the broker object they were instantiated with.
        """
        stub_broker = object()
        factory = BrokerServerProtocolFactory(stub_broker)
        self.assertEquals(factory.broker, stub_broker)


class RemoteBrokerTest(LandscapeTest):

    helpers = [RemoteBrokerHelper]

    def test_wb_set_client(self):
        """
        The C{client} attribute of a L{RemoteBroker} passes a references to
        the connected L{BrokerClient} to the underlying protocol.
        """
        client = object()
        self.remote.client = client
        self.assertIdentical(self.remote._protocol.client, client)

    def test_ping(self):
        """
        The L{RemoteBroker.ping} method calls the C{ping} method of the
        remote L{BrokerServer} instance and returns its result with a
        L{Deferred}.
        """
        result = self.remote.ping()
        return self.assertSuccess(result, True)

    def test_register_client(self):
        """
        The L{RemoteBroker.register_client} method forwards a registration
        request to the remote L{BrokerServer} object.
        """

        def assert_result(result):
            self.assertEquals(result, None)
            [client] = self.broker.get_clients()
            self.assertEquals(client.name, "client")

        sent = self.remote.register_client("client")
        return sent.addCallback(assert_result)

    def test_send_message(self):
        """
        The L{RemoteBroker.send_message} method calls the C{send_message}
        method of the remote L{BrokerServer} instance and returns its result
        with a L{Deferred}.
        """
        message = {"type": "test"}
        self.mstore.set_accepted_types(["test"])

        def assert_response(message_id):
            self.assertTrue(isinstance(message_id, int))
            self.assertTrue(self.mstore.is_pending(message_id))
            self.assertMessages(self.mstore.get_pending_messages(),
                                [message])

        result = self.remote.send_message(message, urgent=True)
        return result.addCallback(assert_response)

    def test_is_message_pending(self):
        """
        The L{RemoteBroker.is_message_pending} method calls the
        C{is_message_pending} method of the remote L{BrokerServer} instance
        and returns its result with a L{Deferred}.
        """
        result = self.remote.is_message_pending(1234)
        return self.assertSuccess(result, False)

    def test_stop_clients(self):
        """
        The L{RemoteBroker.stop_clients} method calls the C{stop_clients}
        method of the remote L{BrokerServer} instance and returns its result
        with a L{Deferred}.
        """
        result = self.remote.stop_clients()
        return self.assertSuccess(result, None)

    def test_reload_configuration(self):
        """
        The L{RemoteBroker.reload_configuration} method calls the
        C{reload_configuration} method of the remote L{BrokerServer}
        instance and returns its result with a L{Deferred}.
        """
        result = self.remote.reload_configuration()
        return self.assertSuccess(result, None)

    def test_register(self):
        """
        The L{RemoteBroker.register} method calls the C{register} method
        of the remote L{BrokerServer} instance and returns its result with
        a L{Deferred}.
        """
        result = self.remote.register()
        return self.assertSuccess(result, None)

    def test_get_accepted_message_types(self):
        """
        The L{RemoteBroker.get_accepted_message_types} method calls the
        C{get_accepted_message_types} method of the remote L{BrokerServer}
        instance and returns its result with a L{Deferred}.
        """
        result = self.remote.get_accepted_message_types()
        return self.assertSuccess(result, self.mstore.get_accepted_types())

    def test_get_server_uuid(self):
        """
        The L{RemoteBroker.get_server_uuid} method calls the C{get_server_uuid}
        method of the remote L{BrokerServer} instance and returns its result
        with a L{Deferred}.
        """
        self.mstore.set_server_uuid("abcde")
        result = self.remote.get_server_uuid()
        return self.assertSuccess(result, "abcde")

    def test_register_client_accepted_message_type(self):
        """
        The L{RemoteBroker.register_client_accepted_message_type} method calls
        the C{register_client_accepted_message_type} method of the remote
        L{BrokerServer} instance and returns its result with a L{Deferred}.
        """

        def assert_response(response):
            self.assertEquals(response, None)
            self.assertEquals(
                self.exchanger.get_client_accepted_message_types(),
                sorted(["type"] + DEFAULT_ACCEPTED_TYPES))

        result = self.remote.register_client_accepted_message_type("type")
        return result.addCallback(assert_response)

    def test_exit(self):
        """
        The L{RemoteBroker.exit} method calls the C{exit} method of the remote
        L{BrokerServer} instance and returns its result with a L{Deferred}.
        """
        result = self.remote.exit()
        return self.assertSuccess(result, None)

    def test_method_call_error(self):
        """
        Trying to call an non-exposed broker method results in a failure.
        """
        result = self.remote._protocol.callRemote(MethodCall,
                                                  name="get_clients",
                                                  args=[],
                                                  kwargs={})
        return self.assertFailure(result, MethodCallError)

    def test_disconnect(self):
        """
        The L{RemoteBroker.disconnect} method closes the connection with
        the broker server.
        """
        self.remote.disconnect()
        result = self.remote.ping()
        return self.assertFailure(result, ConnectionDone)


class RemoteClientTest(LandscapeTest):

    helpers = [BrokerClientHelper]

    def setUp(self):

        def register_client(ignored):

            def set_remote_client(ignored):
                [remote_client] = self.broker.get_clients()
                self.remote_client = remote_client

            registered = self.remote.register_client("test")
            return registered.addCallback(set_remote_client)

        connected = super(RemoteClientTest, self).setUp()
        return connected.addCallback(register_client)

    def test_ping(self):
        """
        The L{RemoteClient.ping} method calls the C{ping} method of the
        remote L{BrokerClient} instance and returns its result with a
        L{Deferred}.
        """
        result = self.remote_client.ping()
        return self.assertSuccess(result, True)

    def test_dispatch_message(self):
        """
        The L{RemoteClient.dispatch_message} method calls the
        C{dispatch_message} method of the remote L{BrokerClient} instance and
        returns its result with a L{Deferred}.
        """
        handler = self.mocker.mock()
        handler({"type": "test"})
        self.mocker.replay()

        def dispatch_message(ignored):

            result = self.remote_client.dispatch_message({"type": "test"})
            return self.assertSuccess(result, True)

        # We need to register a test message handler to let the dispatch
        # message method call succeed
        registered = self.client.register_message("test", handler)
        return registered.addCallback(dispatch_message)

    def test_fire_event(self):
        """
        The L{RemoteClient.fire_event} method calls the C{fire_event} method of
        the remote L{BrokerClient} instance and returns its result with a
        L{Deferred}.
        """
        callback = self.mocker.mock()
        callback(True, kwarg=2)
        self.mocker.replay()
        self.reactor.call_on("event", callback)
        result = self.remote_client.fire_event("event", True, kwarg=2)
        return self.assertSuccess(result, None)

    def test_exit(self):
        """
        The L{RemoteClient.exit} method calls the C{exit} method of the remote
        L{BrokerClient} instance and returns its result with a L{Deferred}.
        """
        result = self.remote_client.exit()
        return self.assertSuccess(result, None)

    def test_method_call_error(self):
        """
        Trying to call an non-exposed client method results in a failure.
        """
        result = self.remote._protocol.callRemote(MethodCall,
                                                  name="get_plugins",
                                                  args=[],
                                                  kwargs={})
        return self.assertFailure(result, MethodCallError)
