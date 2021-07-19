# STP_Simulator

This is a Python applications that simulates the spanning tree algorithm used to prevent loops in an Ethernet switched network.

The application reads the network representation as a DOT file, similar to the one below:


```
// A dot file of a 5-switch network
// Switches' shape and labels are useful for displaying the switch ports

graph MG {
  node [shape=record]

  SW1 [label="<1>1|<2>2|<3>3" mac="00:00:00:00:00:01" priority=32768 xlabel=SW1]
  SW2 [label="<1>1|<2>2|<3>3|<4>4" mac="00:00:00:00:00:02" priority=32768 xlabel=SW2]
  SW3 [label="<1>1|<2>2|<3>3" mac="00:00:00:00:00:03" priority=32768 xlabel=SW3]
  SW4 [label="<1>1|<2>2|<3>3" mac="00:00:00:00:00:04" priority=32768 xlabel=SW4]
  SW5 [label="<1>1" mac="00:00:00:00:00:05" priority=32768 xlabel=SW15]

  SW1:1 -- SW2:3 [speed=100];
  SW1:2 -- SW3:3 [speed=100];
  SW1:3 -- SW4:1 [speed=100];

  SW2:1 -- SW3:1 [speed=100];
  SW2:2 -- SW4:2 [speed=100];
  SW2:4 -- SW4:3 [speed=100];

  SW3:2 -- SW5:1 [speed=100];

}
```

![Network Example](network.png)

The output looks like the following:

```
>python3 stp_simulator.py -i testnet.dot
Bridge: 32769. This bridge is Root.
Port            Role            Status          Cost
------------------------------------------------------------
1               Designated      Forwarding      19
2               Designated      Forwarding      19
3               Designated      Forwarding      19

Bridge: 32770. The Root bridge is 32769.
Port            Role            Status          Cost
------------------------------------------------------------
3               Root Port       Forwarding      19
1               Designated      Forwarding      19
2               Designated      Forwarding      19
4               Designated      Forwarding      19

Bridge: 32771. The Root bridge is 32769.
Port            Role            Status          Cost
------------------------------------------------------------
3               Root Port       Forwarding      19
1               Un-designated   Blocked         19
2               Designated      Forwarding      19

Bridge: 32772. The Root bridge is 32769.
Port            Role            Status          Cost
------------------------------------------------------------
1               Root Port       Forwarding      19
2               Un-designated   Blocked         19
3               Un-designated   Blocked         19

Bridge: 32773. The Root bridge is 32769.
Port            Role            Status          Cost
------------------------------------------------------------
1               Root Port       Forwarding      19
```

log file can be produced to show details:

```
>python3 stp_simulator.py -i testnet.dot -l DEBUG
...

more stp_simulator.log

INFO:root:Reading file: testnet.dot
INFO:root:Simulation starting.
DEBUG:root:Bridge 32769 boots.
DEBUG:root:Bridge 32770 boots.
DEBUG:root:Bridge 32771 boots.
DEBUG:root:Bridge 32772 boots.
DEBUG:root:Bridge 32773 boots.
DEBUG:root:Entering Step: 0
DEBUG:root:Bridge 32769 best BPDU is [32769, 0, 32769, 0].
DEBUG:root:Bridge 32770 best BPDU is [32770, 0, 32770, 0].
DEBUG:root:Bridge 32771 best BPDU is [32771, 0, 32771, 0].
DEBUG:root:Bridge 32772 best BPDU is [32772, 0, 32772, 0].
DEBUG:root:Bridge 32773 best BPDU is [32773, 0, 32773, 0].
DEBUG:root:Bridge 32769 sends BPDU [32769, 0, 32769, 1].
DEBUG:root:Bridge 32769 sends BPDU [32769, 0, 32769, 2].
DEBUG:root:Bridge 32769 sends BPDU [32769, 0, 32769, 3].
DEBUG:root:Bridge 32770 sends BPDU [32770, 0, 32770, 1].
DEBUG:root:Bridge 32770 sends BPDU [32770, 0, 32770, 2].
DEBUG:root:Bridge 32770 sends BPDU [32770, 0, 32770, 4].
DEBUG:root:Bridge 32771 sends BPDU [32771, 0, 32771, 2].
DEBUG:root:Entering Step: 1
DEBUG:root:Bridge 32769 best BPDU is [32769, 0, 32769, 0].
DEBUG:root:Bridge 32770 best BPDU is [32769, 0, 32769, 3].
DEBUG:root:Bridge 32771 best BPDU is [32769, 0, 32769, 3].
DEBUG:root:Bridge 32772 best BPDU is [32769, 0, 32769, 3].
DEBUG:root:Bridge 32773 best BPDU is [32771, 0, 32771, 2].
DEBUG:root:Bridge 32769 sends BPDU [32769, 0, 32769, 1].
DEBUG:root:Bridge 32769 sends BPDU [32769, 0, 32769, 2].
DEBUG:root:Bridge 32769 sends BPDU [32769, 0, 32769, 3].
DEBUG:root:Bridge 32770 sends BPDU [32769, 19, 32770, 1].
DEBUG:root:Bridge 32770 sends BPDU [32769, 19, 32770, 2].
DEBUG:root:Bridge 32770 sends BPDU [32769, 19, 32770, 4].
DEBUG:root:Bridge 32771 sends BPDU [32769, 19, 32771, 2].
DEBUG:root:Entering Step: 2
DEBUG:root:Bridge 32769 best BPDU is [32769, 0, 32769, 0].
DEBUG:root:Bridge 32770 best BPDU is [32769, 0, 32769, 3].
DEBUG:root:Bridge 32771 best BPDU is [32769, 0, 32769, 3].
DEBUG:root:Bridge 32772 best BPDU is [32769, 0, 32769, 3].
DEBUG:root:Bridge 32773 best BPDU is [32769, 19, 32771, 2].
DEBUG:root:Bridge 32769 sends BPDU [32769, 0, 32769, 1].
DEBUG:root:Bridge 32769 sends BPDU [32769, 0, 32769, 2].
DEBUG:root:Bridge 32769 sends BPDU [32769, 0, 32769, 3].
DEBUG:root:Bridge 32770 sends BPDU [32769, 19, 32770, 1].
DEBUG:root:Bridge 32770 sends BPDU [32769, 19, 32770, 2].
DEBUG:root:Bridge 32770 sends BPDU [32769, 19, 32770, 4].
DEBUG:root:Bridge 32771 sends BPDU [32769, 19, 32771, 2].
INFO:root:Simulation completed.
```
