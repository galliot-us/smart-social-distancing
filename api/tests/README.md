###How tests were built

To further improve the tests, I made this file to easily understand how they worked.

The main thing to know is to understand what role fixtures play, especially Config_rollback. 

Config_rollback fixture does the following:
1. setUp: Initialize the app with a different config file (the one with template in the name).
2. Returns the client to make the request and also returns the root of the config file. That root is also returned in order to go directly to that file and check if the changes made from our endpoints were valid.
3. tearDown: Finally, this fixture does a "rollback". What does that mean? Well, before the tearDown code, the config file has probably changed, so, to keep test unit, we copy the original state from the config file and replace it with the already used file. So when the next test starts, you will modify the original configuration from scratch file and it will be easy for us to track what happens.
