---
layout: post
title:  "From radio waves to bits: FSK, Manchester encoding and the inside of a TPMS packet"
date:   2026-11-06 17:00:00 +0530
categories: tpms rf sdr
description: >-
  How a tyre pressure sensor sends its data: a spectrogram of a real packet,
  FSK, Manchester encoding, the fields inside a packet and the Packet Lab.
image:
  path: /assets/images/tpms/tpms-fsk-packets-preview.jpg
  alt: >-
    Spectrogram of a Toyota tyre sensor packet, showing the signal hopping
    between two frequencies
hide_banner: true
---

{% include tpms-series.html %}

In the [last post][part-3] we captured a raw TPMS signal and looked at it in
GNU Radio. We saw the frequency jumping between two levels. In this post, we
will see how data is sent over the radio using frequency shift keying (FSK),
how exactly the bits in the data are encoded using something called Manchester
encoding, and why we use it.

## Seeing the signal: the spectrogram

A spectrogram is a visual representation of a radio signal, with time running
left to right, frequency going up and down and colour showing how strong the
signal is. Here is the same Toyota IQ recording from the [last post][part-3],
taken from the public [rtl_433_tests][rtl433-tests] repo.

![Spectrogram of a Toyota TPMS recording, showing one short packet and a
zoomed-in view of it hopping between two frequencies][spectrogram]{: w="700" }
*Spectrogram of a Toyota TPMS packet from the rtl_433_tests repo*

The top plot is the whole recording, where the sensor stays quiet for a while
and then sends a single packet at around 215 ms that lasts about 8 ms. This
could have been the moment the car started moving, or the recording just
happened to catch a packet at that point. Zooming into it, we can see that the
signal never stays still and keeps hopping between two frequencies about 50 kHz
apart. If you recall how binary works, electronics use 1s and 0s, on and off,
to store and send data. The hops here work the same way, each one carrying a
bit, and how they do that is what FSK is all about.

## What is FSK?

To send data over the air, the sensor has to put its bits onto a radio wave,
and this is called modulation. There are a few ways to do it: change how strong
the wave is (amplitude shift keying, or ASK), how fast it oscillates (frequency
shift keying, or FSK) or where it starts in its cycle (phase shift keying, or
PSK).

![The same bits sent with ASK, where the wave turns on and off, and with
FSK, where the wave switches between a faster and a slower
frequency][ask-fsk]{: w="700" }
*The same bits sent with ASK and with FSK*

ASK is the simplest, with the wave switched on for a 1 and off for a 0. FSK
keeps the wave on all the time and changes its frequency instead, using one
frequency for a 1 and another for a 0. That is exactly what we saw in the
spectrogram, where the Toyota sensor switches between a tone about 25 kHz above
the centre and one about 25 kHz below it.

## Why FSK?

So why do most TPMS sensors, including the ones in my car, use FSK and not the
simpler ASK? The sensor lives inside a spinning wheel, wrapped in a metal rim
and a rubber tyre, so the signal reaching the car keeps getting stronger and
weaker as the wheel turns. With ASK the data is in that strength, so a weak
moment can easily be mistaken for a 0. FSK only cares about which of the two
frequencies is present, which makes it much better at handling these drops and
the noise from everything else on 433 MHz. The radio also transmits at the same
power for the whole packet, which keeps the chip simple and efficient, and that
matters for a sensor running on a coin cell that has to last for years.

## Manchester encoding

Sending bits as two frequencies still leaves one problem. If the sensor sends
a long run of bits like 00000000 or 11111111, the signal just stays on one
frequency, and the receiver has no way to tell where one bit ends and the next
one begins (you can see this in the image below). So FSK on its own is not
enough, and the transmitter and receiver also need some way to stay in sync.
Even if they start in sync, a slight difference between their clocks can make
the receiver count seven or nine bits instead of the eight that were sent.

Manchester encoding fixes this by sending every bit as a change instead of a
level, where a 1 is a transition from low to high in the middle of the bit and
a 0 is a transition from high to low (some systems use the opposite). The cost
is that each bit now takes two symbols, which is a small price for a packet
that is only a few bytes long.

So how does the receiver stay in sync using this? It already knows roughly how
long a bit should be, and it uses these changes as a clock. Every time it sees
the change in the middle of a bit, it lines its own timing up with it and then
waits about one bit length for the next one. If its clock is running slightly
fast or slow, the error gets corrected at every bit instead of building up, so
it stays in sync with the sensor for the whole packet.

![The same bits sent as plain levels, where a run of 0s is a flat line, and
with Manchester encoding, where every bit has a change in the
middle][manchester]{: w="700" }
*The same bits, sent plain and with Manchester encoding*

### Differential Manchester

The Toyota sensor in this post uses a variant called differential Manchester.
There is still a change in the middle of every bit for the clock, but the bit
itself is decided at the start, where a change at the start of the bit means a 0
and no change means a 1 (again, some systems use the opposite). The direction of
the change does not matter at all, the receiver only has to notice whether the
signal changed or not.

Why bother? Choosing between the two is a design decision. With plain
Manchester the sensor and the receiver have to agree on which frequency is the
"high" one, and that is easy when the same company designs both, which is why
plain Manchester works perfectly well in many cars. It gets harder when the
parts come from different makers. A car's receiver is usually built by one
supplier and its sensors by another, and when a sensor dies you might replace
it with an aftermarket one that is sold to work with dozens of car models. If
any of these disagree on which frequency means a 1, plain Manchester decodes
every bit as its opposite, while differential Manchester gives exactly the same
bits because a change is still a change. So with differential Manchester the
receiver only has to spot changes, and nobody has to agree on which way round
the signal is.

![The same bits sent with Manchester and differential Manchester, read by a
receiver that matches the sensor and by one that has the two frequencies the
other way round. Plain Manchester decodes every bit wrong on the mismatched
receiver while differential Manchester gives the same
bits][diff-manchester]{: w="700" }
*When the receiver reads the frequencies the other way round, plain Manchester
gets every bit wrong while differential Manchester still decodes the same bits*

This also explains the hops of two different widths in the spectrogram. When
there is no change at the start of a bit, the last half of one bit and the
first half of the next land on the same frequency and merge into one longer
step.

If you want to see these encodings drawn out step by step, Jacob Schrum's
video [Signal Encoding 1: Digital Signals][encoding-video]{:target="_blank"
rel="noopener"} explains them really well.

## From bits to bytes: inside a packet

Once the receiver has turned the hops into bits, it is left with a short
packet. Every packet starts with a fixed pattern called the preamble, which
gives the receiver something to lock on to before the real data arrives. For
the Toyota sensor in our recording, the data that follows is just 72 bits, or
9 bytes.

![The 72 bits of a Toyota TPMS packet split into its fields: sensor ID,
pressure, temperature, status, inverted pressure and
CRC][toyota-packet]{: w="800" }
*The Toyota packet from our recording, split into its fields*

The first 4 bytes are the sensor ID, `FB0A43E7`, which is the same for every
packet from this sensor and is how the car tells its four tyres apart. Next come
the pressure and the temperature, followed by a few status bits. The sensor then
sends the pressure again with every bit flipped as a quick check, and the last
byte is a CRC, a checksum the receiver uses to throw away any packet that got
damaged on the way.

None of this is in a public datasheet, and the layout above comes from the
[rtl_433 Toyota decoder][toyota-decoder], which people in the community worked
out from their own captures. Turning these bits into actual PSI and °C, and
working out which bits mean what in the first place, is something I had to do
for the sensors on my own car. We will go through all of it in [Part 5][part-5]
and the post after it, where we analyse my car's packets and work out what every
byte means.

## Packet Lab

To make all of this easier to see, I built Packet Lab, a small page that takes
one recorded TPMS transmission and walks through it from the radio signal to
the fields inside it. You can see the frequency hops with the decoded bits
drawn on top of them, and click on any bit or field to zoom into the part of
the signal it came from. It runs
entirely in your browser and uses a few public recordings from the
[rtl_433_tests][rtl433-tests] repo, so you can try it yourself at
[Packet Lab][packet-lab]{:target="_blank" rel="noopener"}.

![Packet Lab showing the Toyota packet: the measured frequency, the high and
low decisions and the decoded bits, with buttons for each
field][packet-lab-img]{: w="800" }
*Packet Lab, showing the same Toyota packet*

The packets also change with what the sensor is doing. Pick the Toyota sensor
that was
[woken up by a workshop tool][lab-wake]{:target="_blank" rel="noopener"} or
[running on a low battery][lab-batt]{:target="_blank" rel="noopener"}, or the
Subaru sensor sending a
[pressure-change alarm][lab-alarm]{:target="_blank" rel="noopener"}, and you
will see the status bits change while the sensor ID stays the same. We will
look at these modes properly in a later post, along with what happened when I
let the air out of my own tyre.

## Coming up

**Coming up in this series:**

- [Decoding the packets from my own car][part-5] (Part 5) and finding the
  pressure and temperature in them
- The different modes of a sensor, and what happens when I let the air out of
  my tyre
- Contributing my decoder to rtl_433
- Building a surveillance lab in my glovebox to collect data on every drive
- Why the sensor measures temperature
- Doing all kinds of data analysis on the data collected

Stay tuned.

[part-3]: {% post_url 2026-11-06-tpms-listening-rtl-sdr %}
[part-2]: {% post_url 2026-11-05-tpms-sensor-hardware %}
[fcc-old]: https://fccid.io/MRXAFFPA4
[fcc-new]: https://fccid.io/MRXBG6FD4
[rtl433-tests]: https://github.com/merbanan/rtl_433_tests
[spectrogram]: /assets/images/tpms/tpms-spectrogram.png
[ask-fsk]: /assets/images/tpms/tpms-ask-vs-fsk.png
[manchester]: /assets/images/tpms/tpms-manchester.png
[diff-manchester]: /assets/images/tpms/tpms-differential-manchester.png
[encoding-video]: https://www.youtube.com/watch?v=i_TLLACZuRk&t=135s
[toyota-packet]: /assets/images/tpms/tpms-toyota-packet.png
[packet-lab]: /packet-lab/
[lab-wake]: /packet-lab/?r=toyota-wake
[lab-batt]: /packet-lab/?r=toyota-lowbatt
[lab-alarm]: /packet-lab/?r=subaru-alarm
[packet-lab-img]: /assets/images/tpms/packet-lab.png
[toyota-decoder]: https://github.com/merbanan/rtl_433/blob/master/src/devices/tpms_toyota.c
[part-5]: {% post_url 2026-11-07-tpms-reverse-engineering %}
