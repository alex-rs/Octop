# Information-base search steps and examples

Use curl + grep to search services, actions, best practices, and data structures. See the "Information base" section of SKILL.md for the entry point and structure.

## Discover the service

Determine the corresponding tccli service name (such as cvm, cbs).

```sh
curl -s https://cloudcache.tencentcs.com/capi/refs/services.md | grep "Cloud Virtual Machine"
```

Reference output:

```
[cvm](service/cvm/index.md) | Cloud Virtual Machine | 2017-03-12 | ...
```

## Search for service best practices

First search whether a best practice matching the current scenario exists.

```sh
curl -s https://cloudcache.tencentcs.com/capi/refs/service/cvm/practices.md | grep reinstall
```

## Search for the action

If the best practices do not cover it, search the service's action list (the action name is the tccli &lt;Action&gt;).

```sh
curl -s https://cloudcache.tencentcs.com/capi/refs/service/cvm/actions.md | grep "resize\|disk"
```

## Read the action documentation

Confirm the parameters, region, and version (tccli generally matches the version automatically):

```sh
curl -s https://cloudcache.tencentcs.com/capi/refs/service/cvm/action/ResizeInstanceDisks.md
```

## Read the data structures

Data structures referenced by the documentation can be examined further:

```sh
curl -s https://cloudcache.tencentcs.com/capi/refs/service/cvm/model/SystemDisk.md
```
