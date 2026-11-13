"""Original guild theme for For the Alliance — war drums, low horns, low strings, baritone chant.

Fully synthesized (no samples), so the guild owns it outright.

Usage:
    python3 tools/music/compose.py            # writes theme.wav next to this script
    ffmpeg -y -i tools/music/theme.wav -af "highpass=f=28,equalizer=f=55:t=o:w=1.2:g=3,equalizer=f=250:t=o:w=1:g=-2,equalizer=f=3500:t=o:w=1.5:g=-3,loudnorm=I=-17:TP=-1.5:LRA=14" -ar 44100 -codec:a libmp3lame -b:a 160k public/theme.mp3

Requires numpy and scipy. Takes about 2 minutes.
"""
import numpy as np
from scipy.signal import fftconvolve, butter, sosfilt

SR = 44100
BPM = 54
BEAT = 60 / BPM
BAR = 4 * BEAT
N_BARS = 22
TOTAL = N_BARS * BAR + 6.0
L = int(TOTAL * SR)
rng = np.random.default_rng(7)

mix = {k: np.zeros((2, L)) for k in ["str", "bass", "brass", "horn", "choir", "timp", "fx", "drum", "chant"]}

NOTE = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6,
        "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}


def hz(n):
    name, octv = n[:-1], int(n[-1])
    midi = 12 * (octv + 1) + NOTE[name]
    return 440.0 * 2 ** ((midi - 69) / 12)


def env(n, a, r, sustain_len):
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(a, 1e-3))
    rel = np.clip((t - sustain_len) / r, 0, 1)
    return e * (1 - rel) ** 2


def place(bus, sig, start, pan=0.0, gain=1.0):
    i = int(start * SR)
    if i >= L:
        return
    sig = sig[: L - i] * gain
    l = np.cos((pan + 1) * np.pi / 4)
    r = np.sin((pan + 1) * np.pi / 4)
    mix[bus][0, i:i + len(sig)] += sig * l
    mix[bus][1, i:i + len(sig)] += sig * r


def additive(f, n, amps, vib_rate=5.2, vib_depth=0.0, vib_delay=0.3, detune=0.0, phase_seed=0):
    t = np.arange(n) / SR
    vib = vib_depth * np.sin(2 * np.pi * vib_rate * t) * np.clip((t - vib_delay) / 0.4, 0, 1)
    inst = f * (2 ** (detune / 1200)) * (1 + vib)
    phase = 2 * np.pi * np.cumsum(inst) / SR
    out = np.zeros(n)
    pr = np.random.default_rng(phase_seed)
    for k, a in enumerate(amps, start=1):
        if f * k > SR / 2 - 2000:
            break
        if np.ndim(a) == 0 and a < 1e-4:
            continue
        out += a * np.sin(k * phase + pr.uniform(0, 2 * np.pi))
    return out


def strings(f, dur, vel=0.6, att=0.9):
    n = int((dur + 1.6) * SR)
    amps = [1 / k * (0.76 ** k) for k in range(1, 16)]
    s = sum(additive(f, n, amps, vib_depth=0.0035, vib_delay=0.15, detune=d, phase_seed=i)
            for i, d in enumerate([-9, -4, 0, 5, 10]))
    return s * env(n, att, 1.5, dur) * vel / 5


def brass(f, dur, vel=0.8, bright=7.0, voices=(-5, 0, 6), att=0.06):
    n = int((dur + 0.8) * SR)
    t = np.arange(n) / SR
    B = 1.5 + bright * vel * np.minimum(1, t / max(att, 0.07)) * (0.75 + 0.25 * np.exp(-t / 0.4))
    out = np.zeros(n)
    for i, d in enumerate(voices):
        tt = t
        vib = 0.003 * np.sin(2 * np.pi * 5.0 * tt) * np.clip((tt - 0.35) / 0.5, 0, 1)
        phase = 2 * np.pi * np.cumsum(f * 2 ** (d / 1200) * (1 + vib)) / SR
        pr = np.random.default_rng(100 + i)
        for k in range(1, 18):
            if f * k > SR / 2 - 2000:
                break
            out += (1 / k) * np.exp(-k / B) * np.sin(k * phase + pr.uniform(0, 6.28))
    return out * env(n, att, 0.7, dur) * vel / len(voices)


def horn(f, dur, vel=0.6, att=0.1):
    return brass(f, dur, vel, bright=2.8, voices=(-4, 3), att=att)


def choir(f, dur, vel=0.5):
    n = int((dur + 1.2) * SR)
    formants = [(700, 110, 1.0), (1220, 140, 0.5), (2600, 220, 0.18)]
    amps = []
    for k in range(1, 40):
        fk = f * k
        a = sum(g * np.exp(-((fk - fc) / bw) ** 2 / 2) for fc, bw, g in formants) + 0.02 / k
        amps.append(a)
    s = sum(additive(f, n, amps, vib_depth=0.006, vib_rate=4.8, vib_delay=0.2, detune=d, phase_seed=50 + i)
            for i, d in enumerate([-12, -5, 2, 9, 15, -18]))
    return s * env(n, 0.7, 1.1, dur) * vel / 6


def timp(f, vel=0.8, length=2.2):
    n = int(length * SR)
    t = np.arange(n) / SR
    s = np.zeros(n)
    for ratio, a, dec in [(1, 1, 0.9), (1.5, 0.5, 0.6), (1.99, 0.3, 0.45), (2.44, 0.15, 0.3)]:
        s += a * np.sin(2 * np.pi * f * ratio * t * (1 + 0.02 * np.exp(-t / 0.05))) * np.exp(-t / dec)
    noise = rng.standard_normal(n) * np.exp(-t / 0.03)
    noise = sosfilt(butter(2, 900, "low", fs=SR, output="sos"), noise)
    return (s + 0.8 * noise) * vel


def cymbal_swell(dur, vel=0.4):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = sosfilt(butter(2, 5000, "high", fs=SR, output="sos"), rng.standard_normal(n))
    return s * (t / dur) ** 3 * vel


def crash(vel=0.35, length=3.5):
    n = int(length * SR)
    t = np.arange(n) / SR
    s = sosfilt(butter(2, 3500, "high", fs=SR, output="sos"), rng.standard_normal(n))
    return s * np.exp(-t / 1.1) * vel


def bar_t(b, beat=0.0):
    return b * BAR + beat * BEAT


# ---------- Harmony ----------
# chord per bar: (bass root, voicing)
CH = {
    "D": ("D", ["D3", "A3", "D4", "F#4", "A4"]),
    "Bm": ("B", ["B2", "F#3", "B3", "D4", "F#4"]),
    "G": ("G", ["G2", "D3", "G3", "B3", "D4"]),
    "A": ("A", ["A2", "E3", "A3", "C#4", "E4"]),
    "Asus": ("A", ["A2", "E3", "A3", "D4", "E4"]),
    "F#m": ("F#", ["F#3", "C#4", "F#4", "A4"]),
    "Em": ("E", ["E3", "B3", "E4", "G4"]),
    "Bb": ("Bb", ["Bb2", "F3", "Bb3", "D4", "F4"]),
    "C": ("C", ["C3", "G3", "C4", "E4", "G4"]),
    "G/D": ("D", ["D3", "G3", "B3", "D4", "G4"]),
}
BASS_OCT = {"D": "D2", "B": "B1", "G": "G1", "A": "A1", "F#": "F#2", "E": "E2", "Bb": "Bb1", "C": "C2"}

form = (["D", "D", "G/D", "Asus"] +                    # intro 0-3
        ["D", "Bm", "G", "A", "D", "F#m", "G", "A"] +  # theme 4-11
        ["Bb", "C", "D", "G", "A", "D"] +              # bridge 12-17
        ["D", "G/D", "D", "D"])                        # outro 18-21

# split-bar chords
split = {10: ("G", "Em"), 11: ("Asus", "A")}

for b, name in enumerate(form):
    halves = [(name, 0, 4)] if b not in split else [(split[b][0], 0, 2), (split[b][1], 2, 2)]
    for cname, beat, beats in halves:
        root, voicing = CH[cname]
        dur = beats * BEAT
        intro = b < 4
        outro = b >= 18
        vel = 0.35 if intro else (0.5 if b < 12 else 0.62)
        if outro:
            vel = 0.45 * (1 - (b - 18) * 0.18)
        for j, nn in enumerate(voicing[:3]):
            if intro and b < 2:
                continue
            place("str", strings(hz(nn), dur, vel), bar_t(b, beat), pan=-0.6 + 1.2 * j / max(1, len(voicing) - 1))
        if b >= 2:
            place("bass", strings(hz(BASS_OCT[root]), dur, vel * 1.1), bar_t(b, beat), pan=0.15)
        # brass chords in theme & bridge: half notes
        if 4 <= b < 18:
            bv = 0.34 if b < 12 else 0.48
            for nn in voicing[:3]:
                place("horn", horn(hz(nn), dur * 0.97, bv, att=0.35), bar_t(b, beat), pan=-0.25)
            place("horn", horn(hz(BASS_OCT[root]) * 2, dur * 0.97, bv * 1.1, att=0.35), bar_t(b, beat), pan=0.2)
        # choir
        if b >= 4:
            cv = 0.55 if 12 <= b < 18 else 0.32
            for nn in voicing[2:]:
                place("choir", choir(hz(nn), dur, cv), bar_t(b, beat), pan=0.3)

# drone & shimmer
for b in range(N_BARS):
    dv = [0.08, 0.13, 0.2, 0.25][b] if b < 4 else (0.28 if b < 18 else 0.28 * (1 - (b - 18) * 0.2))
    place("bass", strings(hz("D2"), BAR, dv), bar_t(b), pan=-0.1)
    place("bass", strings(hz("A2"), BAR, dv * 0.6), bar_t(b), pan=0.1)


# ---------- Timpani ----------
TIMP = {"D": "D2", "B": "B1", "G": "G2", "A": "A1", "F#": "F#2", "E": "E2", "Bb": "Bb1", "C": "C2"}
for b, v in [(4, 0.75), (8, 0.5), (12, 0.8), (14, 0.95), (17, 0.85)]:
    root = CH[form[b]][0]
    place("timp", timp(hz(TIMP[root]), v, 4.0), bar_t(b), pan=0.0)
# intro roll (bar 3) crescendo into theme
rate = 10
n_hits = int(BAR * rate)
for i in range(n_hits):
    place("timp", timp(hz("A1"), 0.04 + 0.35 * (i / n_hits) ** 3, 0.6), bar_t(3) + i / rate, pan=0.0)
# bridge-in roll
for i in range(int(BAR / 2 * rate)):
    place("timp", timp(hz("D2"), 0.04 + 0.4 * (i / (BAR / 2 * rate)) ** 3, 0.6), bar_t(11, 2) + i / rate)
place("fx", cymbal_swell(BAR), bar_t(3), gain=1.0)
place("fx", crash(0.25, 6), bar_t(4))
place("fx", cymbal_swell(BAR / 2, 0.45), bar_t(11, 2))
place("fx", crash(0.3, 6), bar_t(12))
place("fx", cymbal_swell(BAR, 0.4), bar_t(13))
place("fx", crash(0.4, 7), bar_t(14))

# ---------- Melody ----------
# (note or None, beats)
horn_call = [(None, 2), ("A2", 1), ("D3", 1),
             ("A3", 3), ("F#3", 1),
             ("G3", 2), ("E3", 1), ("F#3", 1),
             ("E3", 4)]
theme = [("A4", 1), ("D5", 2), ("E5", 1),
         ("F#5", 3), ("E5", 0.5), ("D5", 0.5),
         ("B4", 2), ("D5", 1), ("G5", 1),
         ("E5", 4),
         ("A4", 1), ("D5", 2), ("E5", 1),
         ("F#5", 2), ("A5", 1), ("F#5", 1),
         ("G5", 2), ("F#5", 1), ("E5", 1),
         ("C#5", 2), ("E5", 2)]
bridge = [("D5", 2), ("F5", 2),
          ("E5", 2), ("G5", 2),
          ("F#5", 4),
          ("G5", 1.5), ("F#5", 0.5), ("E5", 1), ("D5", 1),
          ("E5", 2), ("A4", 1), ("C#5", 1),
          ("D5", 4)]
outro = [("A4", 1), ("D5", 1.5), ("E5", 0.5), ("F#5", 1),
         ("D5", 4),
         ("A4", 2), ("F#4", 2),
         ("D4", 4)]


def play_line(line, start_bar, inst, vel, pan, octave_double=False, legato=0.95):
    t = bar_t(start_bar)
    for nn, beats in line:
        if nn is not None:
            d = beats * BEAT * legato
            if inst == "horn":
                place("horn", horn(hz(nn), d, vel), t, pan=pan)
            else:
                place("brass", brass(hz(nn), d, vel), t, pan=pan)
                if octave_double:
                    lower = nn[:-1] + str(int(nn[-1]) - 1)
                    place("horn", horn(hz(lower), d, vel * 0.8), t, pan=-pan)
        t += beats * BEAT


play_line(horn_call, 0, "horn", 0.6, 0.2)
play_line([("D3", 4), ("D3", 4), ("B2", 2), ("C#3", 2), ("A2", 4)], 0, "horn", 0.32, -0.3)
# soft war-drum heartbeat under the intro, growing
for b in range(4):
    for beat, note in [(0, "D2"), (2, "A1")]:
        v = 0.18 + 0.07 * b + (0.03 if beat == 0 else 0)
        place("timp", timp(hz(note), v, 3.0), bar_t(b, beat))
oct_down = lambda line, k=1: [(n[:-1] + str(int(n[-1]) - k) if n else None, d) for n, d in line]
play_line(oct_down(theme), 4, "horn", 0.7, 0.1)
play_line(oct_down(theme, 2), 4, "horn", 0.5, -0.3)
for (nn, beats), t0 in zip(oct_down(theme), np.cumsum([0] + [b for _, b in theme])[:-1]):
    place("str", strings(hz(nn), beats * BEAT * 0.98, 0.12, att=0.08), bar_t(4) + t0 * BEAT, pan=-0.3)
play_line(oct_down(bridge), 12, "horn", 0.8, 0.1)
for (nn, beats), t0 in zip(bridge, np.cumsum([0] + [b for _, b in bridge])[:-1]):
    lower = nn[:-1] + str(int(nn[-1]) - 2)
    place("horn", horn(hz(lower), beats * BEAT * 0.97, 0.6), bar_t(12) + t0 * BEAT, pan=-0.2)
for (nn, beats), t0 in zip(oct_down(bridge), np.cumsum([0] + [b for _, b in bridge])[:-1]):
    place("str", strings(hz(nn), beats * BEAT * 0.98, 0.15, att=0.08), bar_t(12) + t0 * BEAT, pan=-0.3)
play_line(oct_down(outro), 18, "horn", 0.5, 0.35)


# ---------- War drums ----------
def war_drum(vel, pitch=52, length=2.2, seed=0):
    r = np.random.default_rng(seed)
    n = int(length * SR)
    t = np.arange(n) / SR
    f = pitch * (1 + 1.2 * np.exp(-t / 0.025))
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.7)
    body += 0.35 * np.sin(2 * np.pi * pitch * 2.3 * t) * np.exp(-t / 0.12)
    skin = sosfilt(butter(2, [180, 1600], "band", fs=SR, output="sos"), r.standard_normal(n)) * np.exp(-t / 0.05)
    return np.tanh(2.8 * (body + 0.9 * skin)) / np.tanh(2.8) * vel


def ensemble_drum(vel, seed=0):
    out = np.zeros(int(2.3 * SR))
    for i, (p, off) in enumerate([(40, 0.0), (46, 0.002), (55, 0.004)]):
        d = war_drum(vel * (1.0 if i == 0 else 0.7), p, 2.2, seed * 10 + i)
        o = int(off * SR)
        out[o:o + len(d)] += d
    return out


def rattle(vel, seed=0):
    r = np.random.default_rng(seed)
    n = int(0.5 * SR)
    t = np.arange(n) / SR
    x = sosfilt(butter(2, [1200, 6500], "band", fs=SR, output="sos"), r.standard_normal(n)) * np.exp(-t / 0.09)
    return np.tanh(3 * x) * vel


PAT_HEART = [(0, 1.0), (2, 0.7)]
PAT_MARCH = [(0, 1.0), (1, 0.45), (1.5, 0.35), (2, 0.85), (3, 0.55), (3.5, 0.4)]
PAT_WAR = PAT_MARCH + [(2.5, 0.4), (3.25, 0.45), (3.5, 0.55), (3.75, 0.7)]
seed = 0
for b in range(N_BARS):
    if b < 2:
        pat, scale = [(0, 1.0)], 0.32 + 0.08 * b
    elif b < 4:
        pat, scale = PAT_HEART + [(2.75, 0.4)], 0.45 + 0.08 * (b - 2)
    elif b < 12:
        pat, scale = PAT_MARCH, 0.55 + 0.03 * (b - 4)
    elif b < 18:
        pat, scale = PAT_WAR, 0.8 + 0.04 * (b - 12)
    else:
        pat, scale = PAT_HEART, 0.55 * (1 - (b - 18) * 0.22)
    for beat, v in pat:
        seed += 1
        place("drum", ensemble_drum(scale * v, seed), bar_t(b, beat), pan=0.0)

# bridge-in drum fill
for i in range(8):
    seed += 1
    place("drum", ensemble_drum(0.4 + 0.07 * i, seed), bar_t(11, 2 + i * 0.25))

# ---------- Baritone war chant ----------
VOWELS = {"oh": [(420, 90, 1.0), (760, 120, 0.55), (2450, 200, 0.12)],
          "ah": [(650, 110, 1.0), (1080, 130, 0.5), (2650, 220, 0.15)]}


def men_choir(f, dur, vel, vowel="oh", att=0.4, rel=0.8, voices=(-20, -9, 0, 8, 18)):
    n = int((dur + rel + 0.1) * SR)
    amps = []
    for k in range(1, 50):
        fk = f * k
        a = sum(g * np.exp(-((fk - fc) / bw) ** 2 / 2) for fc, bw, g in VOWELS[vowel]) + 0.05 / k
        amps.append(a)
    s = sum(additive(f, n, amps, vib_depth=0.005, vib_rate=4.5, vib_delay=0.15, detune=d, phase_seed=200 + i)
            for i, d in enumerate(voices))
    t = np.arange(n) / SR
    breath = sosfilt(butter(2, [300, 3000], "band", fs=SR, output="sos"), rng.standard_normal(n)) * 0.04
    return np.tanh(1.6 * (s / len(voices) + breath)) * env(n, att, rel, dur) * vel


CHANT_ROOT = {"D": ("D2", "A2"), "B": ("B1", "F#2"), "G": ("G2", "D3"), "A": ("A2", "E3"), "F#": ("F#2", "C#3"),
              "E": ("E2", "B2"), "Bb": ("Bb1", "F2"), "C": ("C2", "G2")}
# low hum drone from bar 1, growing
for b in range(1, N_BARS):
    root = CH[form[b]][0]
    lo, fifth = CHANT_ROOT[root]
    hv = [0, 0.18, 0.26, 0.34][b] if b < 4 else (0.36 if b < 18 else 0.36 * (1 - (b - 18) * 0.22))
    place("chant", men_choir(hz(lo), BAR, hv, "oh", att=1.2, rel=1.4), bar_t(b), pan=-0.2)
    place("chant", men_choir(hz(fifth), BAR, hv * 0.7, "oh", att=1.2, rel=1.4), bar_t(b), pan=0.2)
# rhythmic "HA" chants: on 1 & 3 in theme, every beat in bridge
for b in range(4, 18):
    root = CH[form[b]][0]
    lo, fifth = CHANT_ROOT[root]
    beats = [0, 2] if b < 12 else [0, 1, 2, 3]
    v = 0.45 + 0.02 * (b - 4) if b < 12 else 0.65 + 0.04 * (b - 12)
    for beat in beats:
        acc = 1.0 if beat in (0, 2) else 0.75
        for note, pan in [(lo, -0.15), (fifth, 0.15)] + ([(lo[:-1] + str(int(lo[-1]) + 1), 0.0)] if b >= 12 else []):
            place("chant", men_choir(hz(note), BEAT * 0.55, v * acc, "ah", att=0.04, rel=0.35), bar_t(b, beat), pan=pan)

# ---------- Mixdown ----------
gains = {"str": 0.45, "bass": 0.45, "brass": 0.0, "horn": 0.75, "choir": 0.0, "timp": 0.3, "fx": 0.15, "drum": 1.0, "chant": 0.55}
PERC = ("drum", "chant", "timp")
dry = sum(mix[k] * g for k, g in gains.items() if k not in PERC)
perc = sum(mix[k] * gains[k] for k in PERC)
dry[:, :] = sosfilt(butter(4, 4200, "low", fs=SR, output="sos"), dry, axis=1)
perc[:, :] = sosfilt(butter(2, 8000, "low", fs=SR, output="sos"), perc, axis=1)


def ir(seed, length=6.0, decay=1.7):
    r = np.random.default_rng(seed)
    n = int(length * SR)
    t = np.arange(n) / SR
    x = r.standard_normal(n) * np.exp(-t / decay)
    x = sosfilt(butter(1, 3200, "low", fs=SR, output="sos"), x)
    x[: int(0.02 * SR)] = 0
    return x / np.sqrt(np.sum(x ** 2))


wet = np.stack([fftconvolve(dry[0], ir(1))[:L], fftconvolve(dry[1], ir(2))[:L]])
pw = np.stack([fftconvolve(perc[0], ir(3, 1.4, 0.32))[:L], fftconvolve(perc[1], ir(4, 1.4, 0.32))[:L]])
out = dry * 0.55 + wet * 0.85 + perc * 0.95 + pw * 0.3
# gentle glue compression (soft clip) + normalize
out = out / np.max(np.abs(out)) * 0.95
out = np.tanh(out * 1.1) / np.tanh(1.1)
# fade tail
fade_n = int(5.0 * SR)
out[:, -fade_n:] *= np.linspace(1, 0, fade_n) ** 2
out = out / np.max(np.abs(out)) * 0.9

import wave
pcm = (out.T * 32767).astype("<i2")
import os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "theme.wav")
with wave.open(OUT, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print("done", TOTAL)
