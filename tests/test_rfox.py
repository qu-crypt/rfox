"""Unit tests for rfox subcommands - no hardware required."""
import os
import shutil
import tempfile
import types
import unittest
from unittest import mock


# ──────────────────────────────────────────────────────────────────────────────
# RFConfig
# ──────────────────────────────────────────────────────────────────────────────

class TestRFConfig(unittest.TestCase):
    def test_defaults(self):
        from rflib.rfox.config import RFConfig
        c = RFConfig()
        self.assertAlmostEqual(c.freq, 433.92e6)
        self.assertEqual(c.modulation, "OOK")
        self.assertEqual(c.drate, 4800.0)

    def test_to_dict_from_dict_roundtrip(self):
        from rflib.rfox.config import RFConfig
        c = RFConfig(freq=915e6, drate=38400, modulation="2FSK")
        self.assertEqual(RFConfig.from_dict(c.to_dict()), c)

    def test_from_dict_ignores_extra_keys(self):
        from rflib.rfox.config import RFConfig
        c = RFConfig.from_dict({"freq": 868e6, "unknown_field": "ignored"})
        self.assertAlmostEqual(c.freq, 868e6)

    def test_summary_contains_freq_and_mod(self):
        from rflib.rfox.config import RFConfig
        s = RFConfig(freq=433.92e6, modulation="OOK").summary()
        self.assertIn("433.9200 MHz", s)
        self.assertIn("OOK", s)

    def test_mutation_does_not_affect_original(self):
        from rflib.rfox.config import RFConfig
        c1 = RFConfig(freq=433e6)
        c2 = RFConfig.from_dict(c1.to_dict())
        c2.freq = 915e6
        self.assertAlmostEqual(c1.freq, 433e6)

    def test_all_modulations_accepted(self):
        from rflib.rfox.config import RFConfig, MOD_NAMES
        for mod in MOD_NAMES:
            c = RFConfig(modulation=mod)
            self.assertEqual(c.modulation, mod)


# ──────────────────────────────────────────────────────────────────────────────
# pcap roundtrip
# ──────────────────────────────────────────────────────────────────────────────

class TestPcap(unittest.TestCase):
    def _frame(self, payload=b'\xde\xad\xbe\xef', freq=433.92e6,
               modulation="OOK", rssi=-72.5):
        from rflib.rfox.pcap import CapturedFrame
        from rflib.rfox.config import RFConfig
        return CapturedFrame(
            ts=1_000_000.5,
            cfg=RFConfig(freq=freq, drate=4800, modulation=modulation),
            rssi=rssi,
            payload=payload,
        )

    def setUp(self):
        self._tmp = tempfile.mktemp(suffix='.pcap')

    def tearDown(self):
        if os.path.exists(self._tmp):
            os.unlink(self._tmp)

    def test_single_frame_roundtrip(self):
        from rflib.rfox import pcap
        f = self._frame()
        pcap.write_one(self._tmp, f)
        frames = list(pcap.read(self._tmp))
        self.assertEqual(len(frames), 1)
        got = frames[0]
        self.assertEqual(got.payload, f.payload)
        self.assertAlmostEqual(got.cfg.freq, f.cfg.freq, delta=1)
        self.assertEqual(got.cfg.modulation, f.cfg.modulation)
        self.assertAlmostEqual(got.rssi, f.rssi, delta=0.2)
        self.assertAlmostEqual(got.ts, f.ts, delta=1e-3)

    def test_multiple_frames_roundtrip(self):
        from rflib.rfox import pcap
        payloads = [bytes([i] * 4) for i in range(5)]
        with pcap.PcapWriter(self._tmp) as w:
            for p in payloads:
                w.write(self._frame(payload=p))
        frames = list(pcap.read(self._tmp))
        self.assertEqual(len(frames), 5)
        for orig, got in zip(payloads, frames):
            self.assertEqual(got.payload, orig)

    def test_append_to_existing_file(self):
        from rflib.rfox import pcap
        pcap.write_one(self._tmp, self._frame(payload=b'\x01'))
        pcap.write_one(self._tmp, self._frame(payload=b'\x02'))
        frames = list(pcap.read(self._tmp))
        self.assertEqual(len(frames), 2)
        self.assertEqual(frames[0].payload, b'\x01')
        self.assertEqual(frames[1].payload, b'\x02')

    def test_all_modulations_preserved(self):
        from rflib.rfox import pcap
        from rflib.rfox.config import MOD_NAMES
        with pcap.PcapWriter(self._tmp) as w:
            for mod in MOD_NAMES:
                w.write(self._frame(modulation=mod))
        frames = list(pcap.read(self._tmp))
        self.assertEqual(len(frames), len(MOD_NAMES))
        for got, mod in zip(frames, MOD_NAMES):
            self.assertEqual(got.cfg.modulation, mod)

    def test_truncated_global_header_raises(self):
        from rflib.rfox import pcap
        with open(self._tmp, 'wb') as f:
            f.write(b'\x00' * 4)
        with self.assertRaises(ValueError):
            list(pcap.read(self._tmp))

    def test_wrong_magic_raises(self):
        from rflib.rfox import pcap
        with open(self._tmp, 'wb') as f:
            f.write(b'\x00' * 24)
        with self.assertRaises(ValueError):
            list(pcap.read(self._tmp))


# ──────────────────────────────────────────────────────────────────────────────
# Presets
# ──────────────────────────────────────────────────────────────────────────────

class TestPresets(unittest.TestCase):
    def test_all_expected_presets_exist(self):
        from rflib.rfox import presets
        for name in ("ev1527", "pt2262", "keeloq", "keyfob315", "srd868", "ism915", "tpms433"):
            self.assertIn(name, presets.names())

    def test_get_returns_rfconfig(self):
        from rflib.rfox import presets
        from rflib.rfox.config import RFConfig
        self.assertIsInstance(presets.get("ev1527"), RFConfig)

    def test_get_returns_independent_copy(self):
        from rflib.rfox import presets
        c1 = presets.get("ev1527")
        c2 = presets.get("ev1527")
        c1.freq = 999e6
        self.assertNotAlmostEqual(c1.freq, c2.freq)

    def test_unknown_preset_raises_key_error(self):
        from rflib.rfox import presets
        with self.assertRaises(KeyError):
            presets.get("does_not_exist_xyz")

    def test_names_are_sorted(self):
        from rflib.rfox import presets
        names = presets.names()
        self.assertEqual(names, sorted(names))

    def test_ev1527_is_433mhz_ook(self):
        from rflib.rfox import presets
        c = presets.get("ev1527")
        self.assertAlmostEqual(c.freq, 433.92e6, delta=1000)
        self.assertEqual(c.modulation, "OOK")

    def test_srd868_is_2fsk(self):
        from rflib.rfox import presets
        c = presets.get("srd868")
        self.assertEqual(c.modulation, "2FSK")


# ──────────────────────────────────────────────────────────────────────────────
# Profiles
# ──────────────────────────────────────────────────────────────────────────────

class TestProfiles(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self._profile_file = os.path.join(self._tmpdir, "profiles.json")
        import rflib.rfox.profiles as _pm
        self._patch = mock.patch.object(_pm, "PROFILE_FILE", self._profile_file)
        self._patch.start()

    def tearDown(self):
        self._patch.stop()
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_save_and_load(self):
        from rflib.rfox import profiles
        from rflib.rfox.config import RFConfig
        profiles.save("myprofile", RFConfig(freq=868e6, modulation="2FSK"))
        loaded = profiles.load("myprofile")
        self.assertAlmostEqual(loaded.freq, 868e6, delta=1)
        self.assertEqual(loaded.modulation, "2FSK")

    def test_load_missing_raises(self):
        from rflib.rfox import profiles
        with self.assertRaises(KeyError):
            profiles.load("doesnotexist")

    def test_list_profiles(self):
        from rflib.rfox import profiles
        from rflib.rfox.config import RFConfig
        profiles.save("a", RFConfig(freq=433e6))
        profiles.save("b", RFConfig(freq=868e6))
        lst = profiles.list_profiles()
        self.assertIn("a", lst)
        self.assertIn("b", lst)

    def test_delete(self):
        from rflib.rfox import profiles
        from rflib.rfox.config import RFConfig
        profiles.save("todel", RFConfig())
        profiles.delete("todel")
        with self.assertRaises(KeyError):
            profiles.load("todel")

    def test_delete_missing_raises(self):
        from rflib.rfox import profiles
        with self.assertRaises(KeyError):
            profiles.delete("nope")

    def test_overwrite_profile(self):
        from rflib.rfox import profiles
        from rflib.rfox.config import RFConfig
        profiles.save("x", RFConfig(freq=433e6))
        profiles.save("x", RFConfig(freq=915e6))
        self.assertAlmostEqual(profiles.load("x").freq, 915e6, delta=1)


# ──────────────────────────────────────────────────────────────────────────────
# _common helpers
# ──────────────────────────────────────────────────────────────────────────────

class TestHexArg(unittest.TestCase):
    def _h(self, s):
        from rflib.rfox.commands._common import hex_arg
        return hex_arg(s)

    def test_plain(self):
        self.assertEqual(self._h("aabbcc"), b'\xaa\xbb\xcc')

    def test_spaces(self):
        self.assertEqual(self._h("aa bb cc"), b'\xaa\xbb\xcc')

    def test_0x_prefix(self):
        self.assertEqual(self._h("0xaabbcc"), b'\xaa\xbb\xcc')

    def test_colons(self):
        self.assertEqual(self._h("aa:bb:cc"), b'\xaa\xbb\xcc')

    def test_uppercase(self):
        self.assertEqual(self._h("AABBCC"), b'\xaa\xbb\xcc')


class TestBinArg(unittest.TestCase):
    def _b(self, s):
        from rflib.rfox.commands._common import bin_arg
        return bin_arg(s)

    def test_value_and_length(self):
        val, length = self._b("1010")
        self.assertEqual(val, 0b1010)
        self.assertEqual(length, 4)

    def test_all_zeros(self):
        val, length = self._b("0000")
        self.assertEqual(val, 0)
        self.assertEqual(length, 4)

    def test_invalid_raises(self):
        from rflib.rfox.commands._common import bin_arg
        with self.assertRaises(ValueError):
            bin_arg("10201")


class TestCfgFromArgs(unittest.TestCase):
    def _args(self, **kw):
        a = types.SimpleNamespace(
            preset=None, profile=None,
            freq=None, drate=None, modulation=None,
            chanbw=None, deviation=None, sync_mode=None,
            sync_word=None, channel=None, pktlen=None,
            power=None, preamble=None, variable_length=False,
        )
        for k, v in kw.items():
            setattr(a, k, v)
        return a

    def test_no_args_gives_defaults(self):
        from rflib.rfox.commands._common import cfg_from_args
        from rflib.rfox.config import RFConfig
        self.assertEqual(cfg_from_args(self._args()), RFConfig())

    def test_freq_override(self):
        from rflib.rfox.commands._common import cfg_from_args
        cfg = cfg_from_args(self._args(freq=915e6))
        self.assertAlmostEqual(cfg.freq, 915e6)

    def test_preset_applied(self):
        from rflib.rfox.commands._common import cfg_from_args
        cfg = cfg_from_args(self._args(preset="ev1527"))
        self.assertAlmostEqual(cfg.freq, 433.92e6, delta=1000)
        self.assertEqual(cfg.modulation, "OOK")

    def test_preset_then_freq_override(self):
        from rflib.rfox.commands._common import cfg_from_args
        cfg = cfg_from_args(self._args(preset="ev1527", freq=434e6))
        self.assertAlmostEqual(cfg.freq, 434e6, delta=100)
        self.assertEqual(cfg.modulation, "OOK")

    def test_variable_length_flag(self):
        from rflib.rfox.commands._common import cfg_from_args
        cfg = cfg_from_args(self._args(variable_length=True))
        self.assertFalse(cfg.fixed_len)


# ──────────────────────────────────────────────────────────────────────────────
# CRC command
# ──────────────────────────────────────────────────────────────────────────────

class TestCRC(unittest.TestCase):
    def _crc(self, *a, **kw):
        from rflib.rfox.commands.crc import _crc
        return _crc(*a, **kw)

    def test_crc8_of_0x01(self):
        # CRC-8/SMBUS (poly=0x07, init=0, xorout=0, no reflect) of b'\x01':
        # crc starts 0x01, shifts left 7 times to 0x80, then XOR with 0x07 -> 0x07
        self.assertEqual(self._crc(b'\x01', 8, 0x07, 0x00, 0x00, False, False), 0x07)

    def test_crc16_xmodem_known_vector(self):
        # CRC-16/XMODEM of b'123456789' = 0x31C3 (well-known test vector)
        result = self._crc(b'123456789', 16, 0x1021, 0x0000, 0x0000, False, False)
        self.assertEqual(result, 0x31C3)

    def test_crc_zero_input(self):
        # zero byte, zero init, zero poly -> zero
        result = self._crc(b'\x00', 8, 0x07, 0x00, 0x00, False, False)
        self.assertEqual(result, 0)

    def test_check_one_self_consistent(self):
        from rflib.rfox.commands.crc import _check_one, CRC8_POLYS, _crc
        poly = CRC8_POLYS[0]
        payload = b'\x01\x02\x03\x04'
        crc_val = _crc(payload, 8, poly[1], poly[2], poly[3], poly[4], poly[5])
        matches = _check_one(payload + bytes([crc_val]), CRC8_POLYS, 8)
        self.assertIn(poly[0], [m[0] for m in matches])

    def test_check_one_too_short_returns_empty(self):
        from rflib.rfox.commands.crc import _check_one, CRC8_POLYS
        self.assertEqual(_check_one(b'\x01', CRC8_POLYS, 8), [])

    def test_check_one_returns_list(self):
        from rflib.rfox.commands.crc import _check_one, CRC16_POLYS
        result = _check_one(b'\x01\x02\x03\x04', CRC16_POLYS, 16)
        self.assertIsInstance(result, list)


# ──────────────────────────────────────────────────────────────────────────────
# Diff command
# ──────────────────────────────────────────────────────────────────────────────

class TestDiff(unittest.TestCase):
    def test_to_bits_ff(self):
        from rflib.rfox.commands.diff import _to_bits
        self.assertEqual(_to_bits(b'\xff'), "11111111")

    def test_to_bits_00(self):
        from rflib.rfox.commands.diff import _to_bits
        self.assertEqual(_to_bits(b'\x00'), "00000000")

    def test_to_bits_aa(self):
        from rflib.rfox.commands.diff import _to_bits
        self.assertEqual(_to_bits(b'\xaa'), "10101010")

    def test_run_two_identical_frames_shows_no_changing_bits(self):
        from rflib.rfox.commands.diff import run
        args = types.SimpleNamespace(input=None, hex=["aabbcc", "aabbcc"], show_frames=False)
        self.assertEqual(run(args), 0)

    def test_run_two_differing_frames(self):
        from rflib.rfox.commands.diff import run
        args = types.SimpleNamespace(input=None, hex=["aabbcc00", "aabbcc01"], show_frames=False)
        self.assertEqual(run(args), 0)

    def test_run_requires_two_frames(self):
        from rflib.rfox.commands.diff import run
        args = types.SimpleNamespace(input=None, hex=["aabbcc"], show_frames=False)
        self.assertEqual(run(args), 2)

    def test_run_from_pcap(self):
        from rflib.rfox import pcap
        from rflib.rfox.pcap import CapturedFrame
        from rflib.rfox.config import RFConfig
        from rflib.rfox.commands.diff import run
        tmp = tempfile.mktemp(suffix='.pcap')
        try:
            with pcap.PcapWriter(tmp) as w:
                for payload in (b'\xaa\xbb\x00', b'\xaa\xbb\x01'):
                    w.write(CapturedFrame(ts=1.0, cfg=RFConfig(), rssi=-70, payload=payload))
            args = types.SimpleNamespace(input=tmp, hex=[], show_frames=False)
            self.assertEqual(run(args), 0)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)


# ──────────────────────────────────────────────────────────────────────────────
# Decode command
# ──────────────────────────────────────────────────────────────────────────────

class TestDecode(unittest.TestCase):
    def test_pwm_decode_10_pairs_give_1(self):
        from rflib.rfox.commands.decode import _pwm_decode
        # 0xAA = 10101010 -> pairs 10 10 10 10 -> "1111"
        self.assertEqual(_pwm_decode(b'\xaa'), "1111")

    def test_pwm_decode_01_pairs_give_0(self):
        from rflib.rfox.commands.decode import _pwm_decode
        # 0x55 = 01010101 -> pairs 01 01 01 01 -> "0000"
        self.assertEqual(_pwm_decode(b'\x55'), "0000")

    def test_pwm_decode_mixed(self):
        from rflib.rfox.commands.decode import _pwm_decode
        # 0x96 = 10010110 -> pairs 10 01 01 10 -> "1001"
        self.assertEqual(_pwm_decode(b'\x96'), "1001")

    def test_run_raw_method(self):
        from rflib.rfox.commands.decode import run
        args = types.SimpleNamespace(
            hex=b'\xaa\x55', input=None,
            frame_index=0, method="raw", hilo=1,
        )
        self.assertEqual(run(args), 0)

    def test_run_manchester_method(self):
        from rflib.rfox.commands.decode import run
        args = types.SimpleNamespace(
            hex=b'\xaa\x55\xaa\x55', input=None,
            frame_index=0, method="manchester", hilo=1,
        )
        self.assertEqual(run(args), 0)

    def test_run_no_source_returns_nonzero(self):
        from rflib.rfox.commands.decode import run
        args = types.SimpleNamespace(
            hex=None, input=None,
            frame_index=0, method="raw", hilo=1,
        )
        self.assertNotEqual(run(args), 0)

    def test_run_auto_method(self):
        from rflib.rfox.commands.decode import run
        args = types.SimpleNamespace(
            hex=b'\x55\xaa', input=None,
            frame_index=0, method="auto", hilo=1,
        )
        self.assertEqual(run(args), 0)


# ──────────────────────────────────────────────────────────────────────────────
# Hardware commands - smoke-tested via FakeRfCat
# ──────────────────────────────────────────────────────────────────────────────

class TestApplyConfig(unittest.TestCase):
    def _dongle(self):
        from rflib.fakedongle_nic import FakeRfCat
        return FakeRfCat()

    def test_apply_ook_config(self):
        from rflib.rfox.dongle import apply_config
        from rflib.rfox.config import RFConfig
        d = self._dongle()
        apply_config(d, RFConfig(freq=433.92e6, drate=4800, modulation="OOK"))
        freq, _ = d.getFreq()
        self.assertAlmostEqual(freq, 433.92e6, delta=10000)

    def test_apply_fsk_config(self):
        from rflib.rfox.dongle import apply_config
        from rflib.rfox.config import RFConfig
        d = self._dongle()
        apply_config(d, RFConfig(freq=868.35e6, drate=4800, modulation="2FSK", deviation=20000))

    def test_apply_preset_config(self):
        from rflib.rfox.dongle import apply_config
        from rflib.rfox import presets
        d = self._dongle()
        apply_config(d, presets.get("srd868"))

    @mock.patch("rflib.rfox.dongle.open_dongle")
    def test_scan_command_has_required_interface(self, _mock):
        from rflib.rfox.commands import scan
        self.assertTrue(callable(getattr(scan, "run", None)))
        self.assertTrue(callable(getattr(scan, "add_args", None)))

    @mock.patch("rflib.rfox.dongle.open_dongle")
    def test_replay_command_has_required_interface(self, _mock):
        from rflib.rfox.commands import replay
        self.assertTrue(callable(getattr(replay, "run", None)))
        self.assertTrue(callable(getattr(replay, "add_args", None)))


if __name__ == "__main__":
    unittest.main()
