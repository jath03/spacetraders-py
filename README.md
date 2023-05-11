# spacetraders-py
A (not auto-generated) python client library for SpaceTraders with caching and token management.


## Examples

```python
from spacetraders import Agent

a = Agent("<token>")
print(a.fleet)
a.save_token()
```


```python
from spacetraders import Agent, WaypointType

a = Agent.load("<agent symbol>")
print(a.credits)
command = a.fleet[0]
wp = next(command.nav.find_type(WaypointType.ORBITAL_STATION))
command.navigate(wp)
```


```python
from spacetraders import Agent, Faction

a = Agent.register("<agent symbol>", Faction.COSMIC)
print(a.contracts)
```
