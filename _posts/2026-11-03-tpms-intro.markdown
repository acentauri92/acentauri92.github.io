---
layout: post
title:  "What is TPMS? Tyre sensors and the most underrated screen in your car"
date:   YYYY-MM-DD 00:00:00 +0530
categories: tpms rf privacy
description: ""
image:
  path: /assets/images/tpms/tpms-intro-preview.jpg
  alt: >-
    Tyre pressure screen on my i20's instrument cluster showing the pressure of
    each tyre in psi
hide_banner: true
---
If you've ever driven a car, you must have seen this or a similar kind of
display.

![Tyre pressure screen and the TPMS warning on my i20's instrument
cluster][dash-collage]{: w="600" }
_Left: the tyre pressure screen. Right: the warning I got when one of my
sensors broke._

In my opinion, this is the most underrated display in cars. It is usually hidden
in the settings somewhere. In my car, I have to press the mode button a few
times before I even get to this screen. The warning screen, as shown in the
image, also pops up on its own when something goes wrong, like a tyre losing
pressure or a problem with the system itself. In my case, it was the second one.
One of my sensors broke, and the car flagged it as a system fault. Normally, it
shows the air pressure of each tyre, like in the image above.

It is necessary to monitor this on a regular basis to keep your tyres in good
condition and make them last longer. It is also quite important for safety, as
under or over inflated tyres can cause loss of control and lead to accidents.
This is the reason why many countries have made the Tyre Pressure Monitoring
System (TPMS) mandatory in cars. For example, in the United States, China and
the EU, it is mandatory for all new cars.

The US was the first to do this. The [TREAD Act][tread-act] was passed in 2000,
after a series of Ford Explorer rollovers in the late 90s were linked to tyre
failures. [FMVSS 138][fmvss-138] is the actual rule that came out of it. It says
the warning light must come on when a tyre drops 25% below the pressure written
on the sticker on your door.

The EU made it mandatory for all new passenger cars sold from November 2014,
under [Regulation 661/2009][eu-661]. China did the same with [GB
26149-2017][gb-26149], and from January 2020 every new passenger car there needs
one.

India is a different story. There is a standard, [AIS-154][ais], which tells
manufacturers how a TPMS must behave if they fit one. But as of writing this, it
is not mandatory for all new cars. My i20 has it because Hyundai chose to put it
in, not because of the law.

But before we get into the details, it helps to know that there are essentially
two types of TPMS.

## Kinds of Tyre Pressure Monitoring Systems (TPMS)

### 1. Indirect TPMS

This is a system where the car uses the wheel speed sensors that are already
there for the ABS (Anti-lock Braking System) to figure out the tyre pressure.
Wait... but how do you take the wheel speed and get the pressure of the tyre?

This is where we use physics.

Inflating or deflating a tyre changes its diameter. Inflating increases it and
deflating decreases it. Now, an under inflated tyre has a smaller diameter, so
it must spin faster than the other wheels to cover the same distance as the
properly inflated tyres. Similarly, an over inflated tyre must spin slower to
cover the same distance. The ABS control unit senses these slight changes in
wheel speed to see if a tyre is inflated properly or not. It does not measure
the actual pressure, but it can tell when one tyre is off compared to the
others. On your car display, it would not show the exact pressure value.
Instead, it would just say that one of your tyres is underinflated. You can see
one example in the image below. This saves cost, as there is no extra hardware
needed inside the wheels. Because of this, many cars still use it today,
especially cheaper ones. Some carmakers, like Audi, Honda and Mazda, even
[switched to it][indirect-comeback] in the early 2010s.

![A TPMS warning on an instrument cluster reading "Check left front tire
pressure"][tpms-warning]{: w="600" }
_An indirect TPMS warning on the instrument cluster. Image:
[Tire Review][tire-review]._

But there is a catch. Since it only compares the wheels to each other, if all
four tyres lose air slowly at the same rate, they all keep spinning at the same
speed and the system does not notice anything. This was a big enough problem
that a US court struck down the first version of FMVSS 138 in 2003, because it
allowed systems that could miss exactly this case.

### 2. Direct TPMS

This is the kind of system my car has. Here, each wheel has its own small sensor
inside the tyre, usually attached to the back of the valve stem, the valve you
use to fill air. The sensor measures the actual pressure and temperature inside
the tyre, and unlike the indirect system, it does not have to guess.

![Diagram of a direct TPMS: a sensor in each tyre sending readings by radio to
a receiver module, which drives the dashboard warning
light][direct-diagram]{: w="600" }
_Direct TPMS: a sensor in each tyre talks to a receiver in the car. Image:
[Performance Plus Tire][ppt-tpms]._

The sensor runs on a small battery sealed inside it. The sensor is designed to
run without draining the battery for 5-10 years. You cannot change the battery,
so when it dies or the sensor breaks, you replace the whole thing. That is
exactly what happened with mine.

So how does the sensor send the pressure data to the car? It cannot use a wire,
because the wheel is spinning and you can't attach a wire to a spinning wheel
without using a complex mechanism. Instead, it sends it over a radio signal to
the control unit. In India and Europe, this is usually on 433.92 MHz, and in the
US it is usually 315 MHz. While you are driving, each sensor periodically sends
a small packet containing the pressure and temperature data to the car's control
unit, which in turn decodes the packet and displays it on the car's display
unit.

And here is the interesting part. These packets are not encrypted. Anyone with a
cheap radio can listen and capture these packets. That is what the rest of this
series is about.

**Coming up in this series:**

- What is inside the sensor hardware
- Replacing the broken sensor in my car
- Why the sensor measures temperature
- Collecting this data using cheap hardware and doing all kinds of data analysis
  on it

Stay tuned.

[tread-act]: https://www.govinfo.gov/link/plaw/106/public/414
[fmvss-138]: https://www.law.cornell.edu/cfr/text/49/571.138
[eu-661]: https://eur-lex.europa.eu/eli/reg/2009/661/oj
[gb-26149]: https://www.chinesestandard.net/PDF.aspx/GB26149-2017
[ais]:https://morth.gov.in/sites/default/files/ASI/524201920344PMAIS_154_F_0.pdf
[tire-review]: https://www.tirereview.com/indirect-tpms-imports/
[indirect-comeback]: https://www.brakeandfrontend.com/indirect-tire-pressure-monitoring-systems-making-a-comeback-on-some-imports/
[ppt-tpms]: https://www.performanceplustire.com/Blog/tire-pressure-monitoring-system-tpms-everything-you-need-to-know

[dash-collage]: /assets/images/tpms/tpms-dashboard-collage.jpg
[direct-diagram]: /assets/images/tpms/direct-tpms-diagram.jpg
[tpms-warning]: /assets/images/tpms/indirect-tpms-warning.jpg
