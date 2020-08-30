

_preComputeAllMasks() on 'delete node', 'delete edge'

    need to rewrite to only set values > edited edge/node idx

make sure right-click to set type sets correct row (at least in nodes)

make type 'empty' show up blank

### search

add search name to constructor and call proper function in run()

be sure to add in

```
if not self.continueSearch:
				break
```

make sure search result table snaps image (Seems to snap for nodes?)



### line profile

fix updating when scrolling slices

### bStack

make sure my changes didn't break lots of other things
 - I am now loading stacks in a list 'self._stackList[]'
 - add and using getImage2(channel, slice)
 
todo: stack contrast widget is always making hist for channel 1
todo: bStatusToolbarWIdget.setMousePosition() need to know the channel


switch displayStateDict['displayThisStack'] = 'ch1' to
	displayStateDict['displayThisStack'] = 1
	displayStateDict['displayThisStack'] = 2
	displayStateDict['displayThisStack'] = 3
	displayStateDict['displayThisStack'] = 'rgb'
	...

