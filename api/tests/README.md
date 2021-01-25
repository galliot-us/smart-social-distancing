###How tests were built

This file aims to clarify how the unitary test work.

The main thing to know is to understand what role fixtures play, especially `Config_rollback`. 

The `Config_rollback` fixture does the following:
1. `setUp`: Initializes the app with a different config file (given from the name of an actual config file).
2. Returns the client to make the request and also the root of the config file. The latter is returned in order to check directly if the endpoints managed to change the said file with the intended updates.
3. `tearDown`: This fixture rollbacks any change made to the config file, so further tests can make use of the same file with the exact same state, and they remain independent of each other.