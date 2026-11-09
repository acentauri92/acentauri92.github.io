---
layout: post
title:  "Reverse engineering my tyre sensors, part 2"
categories: tpms rf sdr
description: >-
  How I found the pressure and temperature in my car's tyre sensor packets with
  a digital tyre pressure gauge, a temperature sensor and a few experiments.
image:
  path: /assets/images/tpms/tpms-pressure-temperature-preview.jpg
  alt: >-
    The 72 bits of my car's tyre sensor packet split into its fields: sensor ID,
    pressure, copy counter, burst number, temperature, mystery byte and checksum
hide_banner: true
---

{% include tpms-series.html %}

<!--
FLAGS FOR DHEERAJ (remove before publishing)
- 0x01 (pressure alert) is kept as a teaser for the modes post.
-->

In the [last post][part-5], using some debugging tools from the rtl_433
repository, we got the raw bits out of the FSK modulated signal from my car.
Using some web based tools, we also decoded the Manchester encoded bits,
eventually getting the raw bytes in the packet. Here are the same four copies
from the front-right tyre again, as shown by [BitBench][bitbench].

```text
86 1c d3 97 | 3d 01 56 1c | bc
86 1c d3 97 | 3d 11 56 1c | cc
86 1c d3 97 | 3d 21 56 1c | dc
86 1c d3 97 | 3d 31 56 1c | ec
```

BitBench is fine for a few packets, but a single drive gives hundreds of them,
so for my experiments I needed something that decodes them all in one go. It
turns out rtl_433's flex decoder can undo the Manchester encoding itself, with
the `decode_mc` option that was added in version 25.12. It follows the
opposite convention to my sensor, so `invert` flips the bits first, and
`preamble` lines the decoding up right after the preamble:

```console
rtl_433 -R 0 -X 'n=my_car,m=FSK_PCM,s=52,l=52,r=150,invert,preamble={16}aaa9,decode_mc' -r recording.cu8
```

On my recording from the last post, this prints the same four packets as
BitBench. Before I found this option, I had written a small Python script that
did the same job. I ran both on a 25 minute drive, and they gave exactly the
same 414 packets, byte for byte. rtl_433 even found one more that my script had
missed.

As mentioned in the earlier posts, during the workshop visit I got a chance to
see the actual sensor when the tyre was removed. From the ID printed on the
sensor and the workshop's OBD tool, we know the ID is represented by the first 4
bytes, in this case `861cd397`. This matches what is printed on the sensor. The
bytes are separated by a line in the text above to show what we know. We also
know the last byte is the checksum, which is used to make sure a packet is not
corrupted. I showed how to calculate it, and how we know it is a checksum, in
the last post.

Now, somewhere in there are the pressure and the temperature, since that is the
whole point of the sensor. There is no datasheet for this sensor. You can try
looking for one, but you won't find any, as manufacturers usually keep this
hidden. The only way to find out which byte is which, at least that is what I
thought, is to change one thing about the tyre at a time, watch which bytes
change, and repeat the same for the temperature. This was the theory. In this
post we will go through how I actually tested the theory and the experiments I
did with my tyres, a digital tyre pressure gauge and a temperature sensor. In
the end, I came up with formulas that turn these raw bytes into pressure values
in psi and temperatures in °C, and we will also see the one byte which made no
sense to me even after the experiments, and is still a mystery.

![A loop of five steps: measure with the gauge and dashboard, drive and record
the raw radio, decode the bits into bytes and check the checksum, compare the
bytes with the gauge, change one thing such as pumping, deflating or heating,
and repeat until the bytes predict the gauge][experiment-cycle]{: w="800" }
*The loop I kept repeating until I could decode the bytes*

## The counter in the sixth byte

The easiest one to start with is the sixth byte, which we already saw changing
in the last post. The sensor sends every reading four times in a row, in a
burst. We know this from the IQ files and the spectrogram we saw in the last
post, where the four packets sit about a tenth of a second apart, and the FCC
report for this sensor also says the same. Sending four copies means that at
least one gets through even if the others are lost. The sixth byte counts these
copies.

A byte is made of two halves of 4 bits each, called nibbles, and each hex digit
is one nibble. In the diagram below, the sixth byte of each copy is written out
in binary. The first nibble goes 0, 1, 2, 3 from one copy to the next, while the
second nibble stays at 1.

![The four copies of a packet from my front-right tyre, with the sixth byte
written out in binary. Its first nibble counts 0, 1, 2 and 3 while the second
nibble stays the same][byte6-counter]{: w="800" }
*The four copies in one burst. Only the first nibble of the sixth byte changes*

So the first nibble is the counter, and it tells the receiver which of the four
copies this is.

But what about the second nibble? A burst is not sent just once. While the car
is moving, the sensor sends a new burst every few seconds to a minute, so the
car always has a fresh reading. In this recording, the next burst from the same
tyre came about 21 seconds later. Its first nibble counts 0 to 3 again, just
like before, but the second nibble is now `2` instead of `1`. To make this easy
to see, the diagram below compares the first copy of each burst. Both have the
counter at 0, so the first nibble is the same in both rows, and the only change
in the sixth byte is the second nibble:

![The first copy of two bursts from the same tyre, 21 seconds apart. In the
sixth byte, the second nibble changes from 1 to 2][byte6-burst]{: w="800" }
*The first copy of two bursts, 21 seconds apart*

The second nibble stays the same within a burst and changes from one burst to
the next, so it works like a burst number. It does not simply go up by one each
time though, the next burst after this one had a `4`, so I am not sure yet what
it means. My guess is that it helps the car tell one burst apart from the next.

That leaves the very first bit of the byte. In both bursts above it is 0, so you
could easily think it is part of the counter too. But a few bursts later, the
same tyre sent a packet where the first bit was 1, so the sixth byte read `87`.
And at the same moment, the fifth byte dropped from `3d` to `3c`. That looks
like two separate changes, but if you write the fifth byte in binary and put the
first bit of the sixth byte at the end of it, they turn into one 9-bit number,
and that number just went down by one, from 122 to 121:

![Two packets from the same tyre a few bursts apart, with the fifth and sixth
bytes written out in binary. As 3d becomes 3c, the last bit of the fifth byte
changes from 1 to 0 and the first bit of the sixth byte changes from 0 to 1.
Together, these 9 bits are the raw pressure, which goes from 122 to
121][byte6-pressure]{: w="800" }
*The fifth byte and the first bit of the sixth byte make one number, which drops
by one step*

So the first bit of the sixth byte is actually part of the pressure, spilling
over from the fifth byte, and one step is a tiny change in pressure. We will
turn this number into psi in the pressure section below. The remaining two bits
of the sixth byte, the second and the fifth one, were 0 in every single packet I
ever received, so I don't know what they are for.

A field crossing from one byte into the next is quite common in these packets.
The Toyota packet we looked at in [Part 4][part-4-packet] does the same thing.
There, a single status bit right after the ID pushes everything one place to
the right, so both its pressure and its temperature start in one byte and end
with the first bit of the next.

This also explains the Abarth log from the start of the last post. Looking at
the [Abarth decoder's source code][abarth-decoder], it reads this whole byte as
the pressure and multiplies it by 1.38 to get kPa. So a `00` became 0 kPa, a
`01` became 1.38 kPa, and an `81`, with that first bit set, became 178.02 kPa.
The "pressure" jumping around in my logs was really this counter and its
neighbours.

## Finding the temperature

For the temperature I suspected the seventh byte. On one of my early
recordings, the car had been parked in a basement all day, and all three
sensors started with exactly the same value, 85. As the drive went on they
spread apart, with the front-right climbing the fastest, just like the plot of
my tyres warming up in the [last post][part-5-wheels]. A value that is the same
for every tyre at rest and goes up as the tyres heat up is exactly how a
temperature should behave.

That told me which byte it was, but not how to turn it into °C. For that I
needed one moment where I knew the real temperature inside the tyre. The
easiest one is a cold start. When a car has been parked overnight and not
driven, the air inside the tyres is at the same temperature as the air outside.
So the next morning, before driving anywhere, I opened the doors to let the car
settle and measured the air temperature with an AHT10, a small temperature and
humidity sensor that I had wired to the Raspberry Pi in my car with a few jumper
wires. It read 26.2 °C. The car's dashboard said 28 °C, but it reads about 2 °C
high, so I did not use it.

You can see the setup in the photo below. The Raspberry Pi sits in the open
glovebox, and the AHT10 hangs from it on a few jumper wires, out in the open
air of the cabin.

![My car's open glovebox with a Raspberry Pi inside and a small AHT10
temperature sensor hanging from it on jumper wires, with a laptop on the
passenger seat][aht10-pi]{: w="450" }
*The Raspberry Pi in the glovebox, with the AHT10 temperature sensor on jumper
wires*

The first packets from my three sensors read 81, 82 and 82 (in decimal). Taking
26.2 away from each gives about 55, so:

```text
temperature (°C) = seventh byte - 55
```

One thing to keep in mind is that the bytes in the packets are written in
hexadecimal (hex), so before putting them into a formula we have to convert them
to normal decimal numbers. In a two-digit hex number, the first digit counts
sixteens and the second counts ones, so `56` means 5 sixteens and 6 ones:

```text
56 (hex) = 5 x 16 + 6 = 86 (decimal)
```

So for our front-right packet, the seventh byte `56` is 86, and the tyre was at
86 - 55 = 31 °C. Interestingly, the Abarth decoder subtracts 50 instead of 55,
so even on the rare packets it did catch, its temperature was 5 °C off. A couple
of weeks later I did the same cold-start test with the new front-left sensor. It
decoded 29.0 °C against 29.1 °C on the AHT10, so the same formula works for it
too.

## Finding the pressure

The pressure was harder. My first try was with the analogue gauge on the tyre
compressor from my car's repair kit (bottom left in the photos below), but it
only reads whole psi and one of its readings was 4 psi off, so I couldn't get
anything useful out of it. That is when I bought the [Stanley digital tyre
pressure gauge][gauge] from the last post (bottom right), which reads to half a
psi.

![Four photos: my laptop on the passenger seat recording the sensors, my car
parked with the tyre compressor and the digital tyre pressure gauge next to the
front wheel, the compressor's analogue gauge up close, and the Stanley digital
tyre pressure gauge on a tyre valve reading 30 psi][gauge-collage]{: w="700" }
*Measuring my tyres. Top: the laptop recording on the passenger seat, and the
compressor and digital tyre pressure gauge by the front wheel. Bottom: the
analogue gauge on the compressor, and the Stanley digital tyre pressure gauge
reading 30 psi*

With the digital tyre pressure gauge, I measured my tyres before and after the
September evening drive from the last post. The fifth byte rose and fell with
the gauge, and together with the first bit of the sixth byte, it makes a 9-bit
number, the raw pressure. The `<< 1` below shifts the fifth byte one place to
the left, and the first bit of the sixth byte fills the gap at the end:

```text
raw pressure = (fifth byte << 1) | (first bit of the sixth byte)
```

Plotting the raw pressure against my gauge readings gave an almost perfect
straight line, and the line that fitted best was:

```text
pressure (psi) = 0.254 x raw pressure + 0.3
```

The 0.254 is how many psi each step of the raw pressure is worth, and the 0.3
is a small offset that shifts the whole line up a little. Both came from my own
measurements. I checked this formula on six new gauge readings the next morning
and on the new front-left sensor at 43 psi, and it was always within half a psi.

But two things looked odd. Why 0.254 and not a round 0.25? And with the offset,
an empty tyre would read 0.3 psi, which makes no sense. Two later accidents
answered both. At the workshop, one of my tyres was let down by mistake until it
was completely empty, and the sensor sent a raw pressure of exactly 0, so there
is no offset. And at the fuel station, my car's dashboard showed exactly the raw
pressure times 0.25 for all four tyres. My gauge simply reads about 0.4 psi
higher than the sensor, and my first formula had picked that up. So the real
formula is:

```text
pressure (psi) = raw pressure x 0.25
```

You can see it in the plot below. All my readings, and the empty tyre, sit on a
straight line through 0, with my gauge readings just a little above it.

![Two plots of my digital tyre pressure gauge readings against the raw pressure
from the sensor. Left: all readings, including the empty tyre at 0, lie on the
line raw times 0.25. Right: a zoom showing the readings sitting slightly above
that line, close to the first fit of 0.254 times raw plus 0.3][gauge-vs-raw]{:
w="800" }
*Digital tyre pressure gauge readings against the raw pressure from the sensor,
with the first fit and the final formula*

For our front-right packet, the fifth byte `3d` is 3 x 16 + 13 = 61 (in hex, the
letters a to f stand for 10 to 15). The first bit of `01` is 0, so the raw
pressure is 61 x 2 + 0 = 122, which is 122 x 0.25 = 30.5 psi.

## The mystery byte

That leaves the eighth byte. In most packets it is `1c`, but every now and then
it is `1d` or `0e` instead, and it never changes within a burst. It does not
follow the pressure or the temperature, and so far none of my experiments have
explained it, so for now it stays a mystery. One more value did show up when I
let the air out of one of my tyres on purpose, and that is for the next post.

## The full packet

Putting it all together, here is everything inside one of my car's packets,
drawn the same way as the Toyota packet in [Part 4][part-4-packet]:

![The 72 bits of my car's packet split into its fields: a 32-bit sensor ID, a
9-bit pressure that takes the whole fifth byte and the first bit of the sixth,
the copy counter and burst number in the rest of the sixth byte, the
temperature, the mystery byte and the checksum][my-car-packet]{: w="800" }
*My car's packet, split into its fields. The two grey bits in the sixth byte
were 0 in every packet*

## Coming up

**Coming up in this series:**

- The different modes of a sensor, and what happens when I let the air out of
  my tyre
- Contributing my decoder to rtl_433
- Building a surveillance lab in my glovebox to collect data on every drive
- Why the sensor measures temperature
- Doing all kinds of data analysis on the data collected

Stay tuned.

[part-5]: {% post_url 2026-11-07-tpms-reverse-engineering %}
[part-4-packet]: {% post_url 2026-11-06-tpms-fsk-packets %}#from-bits-to-bytes-inside-a-packet
[my-car-packet]: /assets/images/tpms/tpms-my-car-packet.png
[bitbench]: https://triq.org/bitbench/
[aht10-pi]: /assets/images/tpms/tpms-aht10-pi-glovebox.jpg
[gauge-vs-raw]: /assets/images/tpms/tpms-gauge-vs-raw.png
[gauge-collage]: /assets/images/tpms/tpms-gauge-collage.jpg
[experiment-cycle]: /assets/images/tpms/tpms-experiment-cycle.png
[byte6-counter]: /assets/images/tpms/tpms-byte6-counter.png
[byte6-burst]: /assets/images/tpms/tpms-byte6-burst.png
[byte6-pressure]: /assets/images/tpms/tpms-byte6-pressure-bit.png
[abarth-decoder]: https://github.com/merbanan/rtl_433/blob/master/src/devices/tpms_abarth124.c
[part-5-wheels]: {% post_url 2026-11-07-tpms-reverse-engineering %}#which-id-is-which-tyre
[gauge]: https://www.amazon.in/dp/B07CL3K5ZB
