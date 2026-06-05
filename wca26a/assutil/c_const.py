#region ADDR

ADDR_VSYNC = 0x00
""" vertical sync set-clear """

ADDR_VBLANK = 0x01
""" vertical blank set-clear """

ADDR_WSYNC = 0x02
""" wait for leading edge of horizontal blank """

ADDR_RSYNC = 0x03
""" reset horizontal sync counter """

ADDR_NUSIZ0 = 0x04
""" number-size player-missile 0 """

ADDR_NUSIZ1 = 0x05
""" number-size player-missile 1 """

ADDR_COLUP0 = 0x06
""" color-lum player 0 and missile 0 """

ADDR_COLUP1 = 0x07
""" color-lum player 1 and missile 1 """

ADDR_COLUPF = 0x08
""" color-lum playfield and ball """

ADDR_COLUBK = 0x09
""" color-lum background """

ADDR_CTRLPF = 0x0A
""" control playfield ball size & collisions """

ADDR_REFP0 = 0x0B
""" reflect player 0 """

ADDR_REFP1 = 0x0C
""" reflect player 1 """

ADDR_PF0 = 0x0D
""" playfield register byte 0 """

ADDR_PF1 = 0x0E
""" playfield register byte 1 """

ADDR_PF2 = 0x0F
""" playfield register byte 2 """

ADDR_RESP0 = 0x10
""" reset player 0 """

ADDR_RESP1 = 0x11
""" reset player 1 """

ADDR_RESM0 = 0x12
""" reset missile 0 """

ADDR_RESM1 = 0x13
""" reset missile 1 """

ADDR_RESBL = 0x14
""" reset ball """

ADDR_AUDC0 = 0x15
""" audio control 0 """

ADDR_AUDC1 = 0x16
""" audio control 1 """

ADDR_AUDF0 = 0x17
""" audio frequency 0 """

ADDR_AUDF1 = 0x18
""" audio frequency 1 """

ADDR_AUDV0 = 0x19
""" audio volume 0 """

ADDR_AUDV1 = 0x1A
""" audio volume 1 """

ADDR_GRP0 = 0x1B
""" graphics player 0 """

ADDR_GRP1 = 0x1C
""" graphics player 1 """

ADDR_ENAM0 = 0x1D
""" graphics (enable) missile 0 """

ADDR_ENAM1 = 0x1E
""" graphics (enable) missile 1 """

ADDR_ENABL = 0x1F
""" graphics (enable) ball """

ADDR_HMP0 = 0x20
""" horizontal motion player 0 """

ADDR_HMP1 = 0x21
""" horizontal motion player 1 """

ADDR_HMM0 = 0x22
""" horizontal motion missile 0 """

ADDR_HMM1 = 0x23
""" horizontal motion missile 1 """

ADDR_HMBL = 0x24
""" horizontal motion ball """

ADDR_VDELP0 = 0x25
""" vertical delay player 0 """

ADDR_VDELP1 = 0x26
""" vertical delay player 1 """

ADDR_VDELBL = 0x27
""" vertical delay ball """

ADDR_RESMP0 = 0x28
""" reset missile 0 to player 0 """

ADDR_RESMP1 = 0x29
""" reset missile 1 to player 1 """

ADDR_HMOVE = 0x2A
""" apply horizontal motion """

ADDR_HMCLR = 0x2B
""" clear horizontal motion registers """

ADDR_CXCLR = 0x2C
""" clear collision latches """

ADDR_CXM0P = 0x30
""" read collision M0-P1, M0-P0 (Bit 7,6) """

ADDR_CXM1P = 0x31
""" read collision M1-P0, M1-P1 """

ADDR_CXP0FB = 0x32
""" read collision P0-PF, P0-BL """

ADDR_CXP1FB = 0x33
""" read collision P1-PF, P1-BL """

ADDR_CXM0FB = 0x34
""" read collision M0-PF, M0-BL """

ADDR_CXM1FB = 0x35
""" read collision M1-PF, M1-BL """

ADDR_CXBLPF = 0x36
""" read collision BL-PF, unused """

ADDR_CXPPMM = 0x37
""" read collision P0-P1, M0-M1 """

ADDR_INPT0 = 0x38
""" read pot port """

ADDR_INPT1 = 0x39
""" read pot port """

ADDR_INPT2 = 0x3A
""" read pot port """

ADDR_INPT3 = 0x3B
""" read pot port """

ADDR_INPT4 = 0x3C
""" read input """

ADDR_INPT5 = 0x3D
""" read input """

ADDR_SWCHA = 0x0280
""" Port A; input or output (read or write) """

ADDR_SWACNT = 0x0281
""" Port A DDR, 0= input, 1=output """

ADDR_SWCHB = 0x0282
""" Port B; console switches (read only) """

ADDR_SWBCNT = 0x0283
""" Port B DDR (hardwired as input) """

ADDR_INTIM = 0x0284
""" Timer output (read only) """

ADDR_INSTAT = 0x0285
""" Timer Status (read only, undocumented) """

ADDR_TIM1T = 0x0294
""" set 1 clock interval (838 nsec/interval) """

ADDR_TIM8T = 0x0295
""" set 8 clock interval (6.7 usec/interval) """

ADDR_TIM64T = 0x0296
""" set 64 clock interval (53.6 usec/interval) """

ADDR_T1024T = 0x0297
""" set 1024 clock interval (858.2 usec/interval) """

ADDR_ENTRY = 0xFFFC
""" Cart Entrypoint (16bit pointer) """

ADDR_BREAK = 0xFFFC
""" Cart Breakpoint (16bit pointer) """

#endregion

#region ROM

ROM_BEG = 0xF000
""" Starting address of cartridge ROM """

ROM_END = 0x10000
""" Ending address of cartridge ROM """

ROM_SIZE = 0x10000 - 0xF000
""" Size of a normal 4K cartridge """

#endregion