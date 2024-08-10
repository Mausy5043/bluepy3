Your issue may already be reported!
Please search on the [issue tracker](https://github.com/Mausy5043/bluepy3/issues?q=is%3Aissue+) before creating one.

Please use [stackoverflow](https://stackoverflow.com) for code/coding questions.

<!--- Provide a general summary of the issue in the Title above  -->

**I'm submitting a ...**
<!--- insert an 'x' in the appropriate box like this: [x]  -->
  - [ ] bug report
  - [ ] feature request
  - [ ] support request => Please do not submit support request here, see note at the top of this template.

## Expected Behavior
<!--- If you're describing a bug, tell us what should happen  -->
<!--- If you're suggesting a change/improvement, tell us how it should work  -->

## Current Behavior
<!--- If describing a bug, tell us what happens instead of the expected behavior  -->
<!--- If suggesting a change/improvement, explain the difference from current behavior  -->

## Possible Solution
<!--- Not obligatory, but we appreciate your help improving this project.  -->
<!--- Please refer to CONTRIBUTING.md on how to suggest a fix for the bug,  -->
<!--- or ideas on how to implement the addition or change.  -->

## Steps to Reproduce (for bugs)
<!--- Provide a link to a live example, or an unambiguous set of steps to  -->
<!--- reproduce this bug. Include code to reproduce, if relevant  -->
1.
2.
3.
4.

## Context
<!--- How has this issue affected you? What are you trying to accomplish?  -->
<!--- Providing context helps us come up with a solution that is most useful in the real world  -->

## Your Environment
<!--- Include as many relevant details about the environment you experienced the bug in  -->

* OS (Distribution/version/flavour)
```
hostnamectl | tail -n 3
<!--- put output here  -->

journalctl --boot 0 | head
<!--- put output here  -->

cat /proc/version
<!--- put output here  -->
```

* Software stack
<!--- If your problem occurs on different software stacks, there may be different causes. -->
<!--- Please consider creating separate issues for different software stacks. -->
```
bluetoothctl --version
<!--- put output here  -->

python --version
<!--- put output here  -->

python -m pip freeze |grep blue
<!--- put output here  -->

find / -name bluepy3-helper 2>/dev/null
<!--- put output here  -->

find / -name bluepy3-helper 2>/dev/null -exec {} version \;
<!--- put output here  -->

grep "^version" $(find / -name pyproject.toml 2>/dev/null |grep bluepy3)
<!--- put output here  -->
```

* Hardware platform and stack (brands/makes/models/versions/product URLs)
<!--- If your problem occurs on different hardware platforms, there may be different causes.  -->
<!--- Please consider creating separate issues for different hardware platforms.  -->
<!--- Example: Raspberry Pi Model 3B+ (https://www.raspberrypi.org/)  -->
<!---          - Add details about the Bluetooth hardware  -->
<!---          - Does the Bluetooth modem support BLE ?  -->
<!---          - Which device are you connecting to? (brand/make/model/version/product URL)  -->
