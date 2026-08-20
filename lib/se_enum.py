
class BtnSE(tuple):
    __slots__ = ()

    def __new__(cls, name: str):
        return super().__new__(cls, (name,))

    @property
    def name(self) -> str:
        return self[0][0]


class SlideSE(BtnSE):
    __slots__ = ()


class ChainSlideSE(BtnSE):
    __slots__ = ()

    def __new__(cls, name: str, success: str, first: str, failure: str, sub: str):
        return super().__new__(cls, (name, success, first, failure, sub))

    @property
    def success(self) -> str:
        return self[0][1]

    @property
    def first(self) -> str:
        return self[0][2]

    @property
    def failure(self) -> str:
        return self[0][3]

    @property
    def sub(self) -> str:
        return self[0][4]


BTN_SE_MAP: tuple[BtnSE, ...] = (
    BtnSE('dummy'),
    BtnSE('01_button1'),
    BtnSE('02_button2'),
    BtnSE('03_button3'),
    BtnSE('05_button5'),
    BtnSE('06_button6'),
    BtnSE('41_button9'),
    BtnSE('42_button10'),
    BtnSE('43_button11'),
    BtnSE('44_button12'),
    BtnSE('08_hh1'),
    BtnSE('08_hh1_2nd'),
    BtnSE('10_hh3'),
    BtnSE('10_hh3_2nd'),
    BtnSE('20_wataiko'),
    BtnSE('20_wataiko_2nd'),
    BtnSE('21_wood1'),
    BtnSE('21_wood1_2nd'),
    BtnSE('22_wood2'),
    BtnSE('22_wood2_2nd'),
    BtnSE('23_stick'),
    BtnSE('24_tambourine'),
    BtnSE('24_tambourine_2nd'),
    BtnSE('28_bell3'),
    BtnSE('29_clap'),
)

SLIDE_SE_MAP: tuple[SlideSE, ...] = (
    SlideSE('slide_se13'),
    SlideSE('slide_se01'),
    SlideSE('slide_se05'),
    SlideSE('slide_se07'),
    SlideSE('slide_se11'),
    SlideSE('slide_se25'),
    SlideSE('slide_se26'),
)

CHAINSLIDE_SE_MAP: tuple[ChainSlideSE, ...] = (
    ChainSlideSE('slide_ok03', 'slide_ok03', 'slide_long02a', 'slide_ng03', 'slide_button08'),
    ChainSlideSE('slide_ok02', 'slide_ok02', 'slide_long01a', 'slide_ng03', 'slide_button08'),
    ChainSlideSE('slide_ok04', 'slide_ok04', 'slide_long06a', 'slide_ng03', 'slide_button08'),
    ChainSlideSE('slide_ok01', 'slide_ok01', 'slide_long08a', 'slide_ng03', 'slide_button08'),
    ChainSlideSE('slide_ok08', 'slide_ok08', 'slide_long01b', 'slide_ng03', 'slide_button08'),
    ChainSlideSE('slide_ok02', 'slide_ok02', 'slide_long02b', 'slide_ng03', 'slide_button08'),
    ChainSlideSE('slide_ok08', 'slide_ok08', 'slide_long02c', 'slide_ng03', 'slide_button08'),
    ChainSlideSE('slide_ok03', 'slide_ok03', 'slide_long06b', 'slide_ng03', 'slide_button08'),
    ChainSlideSE('slide_ok04', 'slide_ok04', 'slide_long08b', 'slide_ng03', 'slide_button08'),
    ChainSlideSE('slide_ok08', 'slide_ok08', 'slide_long12a', 'slide_ng03', 'slide_button08'),
    ChainSlideSE('slide_ok09', 'slide_ok09', 'slide_long12b', 'slide_ng03', 'slide_button08'),
    ChainSlideSE('slide_ok09', 'slide_ok09', 'slide_long13a', 'slide_ng03', 'slide_button08'),
    ChainSlideSE('slide_ok09', 'slide_ok09', 'slide_long14a', 'slide_ng03', 'slide_button08'),
    ChainSlideSE('slide_ok02', 'slide_ok02', 'slide_long15a', 'slide_ng03', 'slide_button08'),
    ChainSlideSE('slide_ok06', 'slide_ok06', 'slide_long15b', 'slide_ng03', 'slide_button08'),
    ChainSlideSE('slide_ok07', 'slide_ok07', 'slide_long16a', 'slide_ng03', 'slide_button08'),
    ChainSlideSE('slide_ok08', 'slide_ok08', 'slide_long17a', 'slide_ng03', 'slide_button08'),
    ChainSlideSE('slide_ok09', 'slide_ok09', 'slide_long19a', 'slide_ng03', 'slide_button08'),
)