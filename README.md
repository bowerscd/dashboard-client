This project is a python client to HappyLeaves' aoe2 spectator dashboard.

It is not endorsed nor developed by HappyLeaves, and has no relation to the spectator dashboard
other than consuming the underlying websocket connection.

As such, **it may be broken at any moment**, and production applications **should not take a dependency on this client.**

All dataclasses and packets were analyzed via reverse engineering the raw data being sent. You can see the samples under the event class.
