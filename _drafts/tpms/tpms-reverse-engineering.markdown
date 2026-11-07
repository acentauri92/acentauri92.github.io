---
layout: post
title:  "Reverse engineering my car's tyre sensors"
categories: tpms rf sdr
description: >-
  How I reverse engineered my car's tyre sensors with an RTL-SDR, rtl_433's flex
  decoder and BitBench, from raw radio signals to a checked packet.
image:
  path: /assets/images/tpms/tpms-reverse-engineering-preview.jpg
  alt: >-
    Plot of temperature against time for three of my tyre sensors on a drive,
    with the front-right tyre warming up faster than the two rear ones
hide_banner: true
---

As I mentioned in [Part 2][part-2], I did not know anything about TPMS at
first. Once I did, I wanted to see what my own car was transmitting, so I looked
for IDs that kept repeating every day in my logs. My receiver travels with me in
the car, so in theory it should pick up every packet my tyres send, and my car's
IDs should show up again and again. Some IDs did repeat, but most of the time
there was nothing like that.

The reason was that rtl_433 had no decoder for my car's sensors, so it quietly
dropped almost all of their packets. Once in a while a packet happened to pass
the checks of a decoder written for a completely different sensor, the one in
the [Fiat Abarth 124 Spider][abarth-decoder], and rtl_433 printed it as an
Abarth with a pressure that made no sense, which is expected because that
decoder was never meant for my car's sensors. Here are three of those packets
from my logs, all from the same tyre on a single drive on 9 July 2026 (trimmed
to the main fields):

```text
date        time      model             id        pressure_kPa  temperature_C
2026-07-09  11:02:52  Abarth-124Spider  861cd61b  0.0           35.0
2026-07-09  11:04:01  Abarth-124Spider  861cd61b  178.02        35.0
2026-07-09  11:04:50  Abarth-124Spider  861cd61b  1.38          35.0
```

The same tyre goes from 0 to 178 kPa and back to almost 0 within two minutes,
while the temperature does not change at all. A real tyre can't do that, so the
decoder was clearly reading the wrong bits as pressure. When I went back through
all the data, including these odd decodes, three IDs starting with `861cd` stood
out. They showed up on 45 of the 57 days I had driven until then, usually within
minutes of starting a drive and with a higher signal-to-noise ratio (SNR) than
everything else around, and they followed me across the city. My car had only
three working sensors at that point, since the fourth one had broken off, so
three IDs was exactly what I expected.

## Why reverse engineer it?

Finding my IDs was only half the answer, because without a decoder I still
couldn't read anything useful from them. My dashboard only shows the pressure,
but as we saw in [Part 2][part-2], the sensor also measures temperature and
sends it in every packet, and I wanted to see that too. There was also a bigger
reason. I was collecting data from thousands of other tyres, and my own car is
the only one I can walk up to with a tyre gauge and check. If I could decode it
properly, it would become the ground truth for everything else I wanted to do
with the data. And since nobody had decoded this sensor before, whatever I
learned could go back into rtl_433 so that anyone with an SDR could read these
sensors too.

So I set out to work out what every byte in my car's packets meant.

## Which ID is which tyre?

Knowing my three IDs was a good start, but I also wanted to know which tyre
each one belonged to. In [Part 2][part-2] I mentioned that I had worked this
out before the workshop visit, just by listening to my car and doing a few
experiments, so here is how. At this point my front-left sensor was the broken
one, so all of these experiments were done with just the other three.

On one September evening, I measured all four tyres with a digital tyre gauge
(yes, I bought a [Stanley digital gauge][gauge] just for this), once cold before
a drive and once warm after it, with my receiver recording the whole drive. My
rear-left tyre happened to be about 5 psi higher than the others, at 37 psi on
my gauge, and this became my reference point. Even before I knew how to convert
anything, one of the IDs, `861cd61b`, had a clearly higher value in the bytes I
suspected were pressure, so that one had to be the rear-left.

The other two were told apart by temperature. My i20 is front-wheel drive, so
the front tyres do the pulling, most of the steering and most of the braking,
and in theory they should heat up more than the rear ones. To test this I went
on a drive with lots of turns, acceleration and braking, and you can see it
clearly in the bottom half of the plot below. All three tyres warm up as the
drive goes on, but `861cd397` climbs much faster than the other two, while
`861cd809` and `861cd61b` rise slowly together just like two rear tyres should.
So `861cd397` was the front tyre and `861cd809` a rear one. The rear-left was
already taken and the front-left had no sensor, which left `861cd397` on the
front-right and `861cd809` on the rear-right.

![Two plots of my three sensors during a drive. Top: the bytes I suspected were
pressure, with 861cd61b clearly higher than the other two. Bottom: temperature
in °C, which rises over the drive for all three and much faster for 861cd397,
the front tyre][three-sensors]{: w="700" }
*My three sensors on a drive, labelled with the positions I worked out. Top:
the rear-left sits far above the others in the suspected pressure bytes. Bottom:
the front tyre warms up much faster than the two rear ones*

A few days later I went to the workshop to get the new sensor fitted, and their
OBD tool showed the ID registered for each wheel. All three matched what I had
worked out. The same screen also showed that the broken front-left sensor had
been `861cd414`, which is why I never saw it in my logs, and it gave me the ID
of the new sensor, `9187740a`, which I have been tracking ever since.

| Wheel       | Sensor ID  | How I worked it out                       |
|-------------|------------|-------------------------------------------|
| Rear-left   | `861cd61b` | Highest pressure, matching the tyre gauge |
| Front-right | `861cd397` | Heated up the most on the drive           |
| Rear-right  | `861cd809` | Warmed up like a rear tyre                |
| Front-left  | `9187740a` | New sensor, read from the OBD tool        |

## Getting the bits out

Before decoding anything, I first needed to know how my sensors send their
bits. As we saw in [Part 4][part-4], there are two common ways, ASK, where the
signal switches on and off, and FSK, where it hops between two frequencies.
Three things pointed to FSK. rtl_433 comes with an analyzer, `rtl_433 -A`, that
looks at a recording and guesses the modulation. For my car it saw the whole
9.4 ms packet as one single long pulse (trimmed output):

```console
$ rtl_433 -A recording.cu8
Analyzing pulses...
Total count:    1,  width: 9.39 ms   (9389 S)
Pulse width distribution:
 [ 0] count:    1,  width: 9389 us [9389;9389]   (9389 S)
...
Guessing modulation: Single pulse detected. Probably Frequency Shift Keying or just noise...
```

That makes sense, because in FSK the signal strength stays the same and only the
frequency changes, so there are no on and off pulses to see. The spectrogram
below shows the same thing, a signal hopping between two frequencies about
80 kHz apart, just like the Toyota packet in Part 4. And the FCC test report for
my sensor, which we looked at in [Part 2][part-2], lists the modulation as FSK.

![Spectrogram of a recording of my front-right tyre sensor. Top: the whole
recording with four short packets. Bottom: a 2 ms zoom into the first packet,
where the signal hops between two frequencies about 80 kHz
apart][my-spectrogram]{: w="700" }
*A burst of four packets from my front-right tyre, and a zoom into the first one
showing the two FSK frequencies*

Next I needed something that could turn that FSK signal into bits. rtl_433 has
hundreds of decoders, but each one is written for a specific sensor and knows
exactly what its bits mean, and none of them was written for mine. For cases
like this, rtl_433 also has a flex decoder. It is a general-purpose decoder you
describe on the command line instead of writing in C, where you tell it the
modulation, how long each symbol lasts and how a packet ends, and it slices the
signal into raw bits without knowing what any of them mean. This is exactly the
approach the rtl_433 [guide to analyzing unknown devices][rtl433-analyze]
recommends, and the full syntax is in the [flex decoder docs][rtl433-flex].

The one thing I still needed was the symbol length, how long each half-bit
lasts. I didn't measure it at first, I just guessed. Many FSK tyre sensors in
rtl_433, including the Abarth and Ford decoders that had been catching stray
packets from my car, use 52 µs, so I tried that and ran rtl_433 on one of my
recordings with all its own decoders switched off and a flex decoder of my own:

```console
rtl_433 -R 0 -X 'n=mycar,m=FSK_PCM,s=52,l=52,r=150' -r recording.cu8
```

`-R 0` turns off every built-in decoder and `-X` adds the flex decoder, where
`n=mycar` is just the name it prints next to anything it finds, `m=FSK_PCM`
says the signal is FSK with every symbol the same length, `s=52,l=52` sets that
length to 52 µs and `r=150` ends a packet after 150 µs of silence. The guess
worked, and out came four clean rows, one for each copy of the packet the sensor
sends in a burst:

```text
{178}55555556956956a5a65a966a5aa65556666956a59aa50
{178}55555556956956a5a65a966a5aa65656666956a5a5a50
{178}55555556956956a5a65a966a5aa65956666956a5a6a50
{178}55555556956956a5a65a966a5aa65a56666956a5a9a50
```

Later I went back to the zoomed spectrogram above to check the guess, and the
shortest hops there do last about 52 µs, so it was not just luck.

These are still Manchester bits, not data. The run of `5`s at the start is
`0101 0101 ...` in binary, the preamble the receiver uses to lock on, and it
ends with a `0110` that breaks the pattern and marks where the data begins. The
144 bits after that are the actual packet, still Manchester encoded, so every
pair of bits makes one real bit, `10` for a 1 and `01` for a 0.

The flex decoder stops at raw bits and has no option to undo Manchester, but you
don't need to write any code for this part. [BitBench][bitbench], a browser tool
from the rtl_433 developers, takes rows like these and decodes them for you, and
their [guide to analyzing unknown devices][rtl433-analyze] recommends putting
your codes into it.

Here is what I set on the page:

- **Input:** the four `{178}...` rows from rtl_433, pasted as they are. The
  `{178}` tells BitBench each row is 178 bits long.
- **Coding:** Manchester (G.E. Thomas), which turns every pair of bits into one.
- **Show:** Hex, so the result is easy to compare with the bytes below.
- **Format string:** `16x ID:32h 8h 8h 8h 8h CHECKSUM:8h`, which skips the
  16 bits that come from the preamble, prints the 4-byte ID in one piece and
  then the remaining bytes one by one.

Everything else, like alignment, shift, invert and calculation, I left at its
default.

![BitBench in the browser decoding my four rows with Manchester (G.E. Thomas)
coding, each showing the ID 861cd397 followed by the other bytes and the
checksum][bitbench-img]{: w="900" }
*My four rows decoded in BitBench with Manchester (G.E. Thomas), with the ID
right at the front of each one*

But should `10` be a 1 or a 0? As we saw in [Part 4][part-4-manchester], there
is no single rule, and different systems do it differently. BitBench has both
options, Manchester (G.E. Thomas), where `10` is a 1, and Manchester (IEEE
802.3), where `01` is a 1, so I didn't have to guess. I tried both and only G.E.
Thomas gave an ID I had already found in my logs. rtl_433's own Manchester
decoder, which I used later, follows IEEE 802.3, and with it my sensor's ID
comes out as `79e32c68` instead of `861cd397`. Decoded with the right option,
the 144 bits become 72 bits, or 9 bytes:

```text
86 1c d3 97 3d 01 56 1c bc
86 1c d3 97 3d 11 56 1c cc
86 1c d3 97 3d 21 56 1c dc
86 1c d3 97 3d 31 56 1c ec
```

The first four bytes are the sensor's ID, `861cd397`, the front-right tyre. Out
of the remaining five bytes, only the sixth and the last one change between the
four copies. The last one is the subject of the next section, and the rest I
will come back to in the next post.

## Cracking the checksum

The last byte of every packet is a checksum, a small number calculated from the
other bytes so the receiver can tell if anything got corrupted on the way (Ben
Eater's video [Checksums and Hamming distance][checksum-video]{:target="_blank"
rel="noopener"} explains them really well). The four copies above gave away how
it works. Between copies, the sixth byte goes up by `0x10` (`01`, `11`, `21`,
`31`) and the last byte goes up by exactly the same amount (`bc`, `cc`, `dc`,
`ec`). That is what you would expect if the last byte is simply the sum of all
the others.

And it is. Add up the first eight bytes and keep only the lowest byte of the
result:

```text
86 + 1c + d3 + 97 + 3d + 01 + 56 + 1c = 2bc  ->  bc
```

which is exactly the last byte. This held for every single packet from all
my sensors. It also explains the Abarth mix-up from the start of this post.
The Abarth decoder checks its packets by XOR-ing the bytes together instead of
adding them, so almost none of my packets passed. Once in a while one passed
by pure chance, and those were the ones that showed up in my logs as an Abarth.

## Coming up

So I could now find my car's packets, pull the bits out of them and check that
they were not corrupted. What the remaining bytes actually mean is the next
step.

**Coming up in this series:**

- Turning the bytes into pressure and temperature with the help of a tyre gauge,
  and the one byte I couldn't explain
- The different modes of a sensor, and what happens when I let the air out of
  my tyre
- Contributing my decoder to rtl_433
- Building a surveillance lab in my glovebox to collect data on every drive
- Why the sensor measures temperature
- Doing all kinds of data analysis on the data collected, with a lot more
  interesting plots like the one of my tyres warming up in this post

Stay tuned.

[part-2]: {% post_url 2026-11-05-tpms-sensor-hardware %}
[part-4]: {% post_url 2026-11-06-tpms-fsk-packets %}
[checksum-video]: https://www.youtube.com/watch?v=ppU41c15Xho
[bitbench]: https://triq.org/bitbench/
[bitbench-img]: /assets/images/tpms/tpms-bitbench.png
[rtl433-analyze]: https://triq.org/rtl_433/ANALYZE.html
[rtl433-flex]: https://triq.org/rtl_433/OPERATION.html#flex-decoder
[part-4-manchester]: {% post_url 2026-11-06-tpms-fsk-packets %}#manchester-encoding
[abarth-decoder]: https://github.com/merbanan/rtl_433/blob/master/src/devices/tpms_abarth124.c
[my-spectrogram]: /assets/images/tpms/tpms-my-car-spectrogram.png
[three-sensors]: /assets/images/tpms/tpms-three-sensors-warming.png
[gauge]: https://www.amazon.in/dp/B07CL3K5ZB
