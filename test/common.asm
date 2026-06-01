@ifndef COMMON
@define COMMON

; Here are some common definitions
; Shamelessly taken from https://problemkaputt.de/2k6specs.htm

; TIA - WRITE ADDRESS SUMMARY (Write only)
@define VSYNC   $00 ; ......1.  vertical sync set-clear
@define VBLANK  $01 ; 11....1.  vertical blank set-clear
@define WSYNC   $02 ; <strobe>  wait for leading edge of horizontal blank
@define RSYNC   $03 ; <strobe>  reset horizontal sync counter
@define NUSIZ0  $04 ; ..111111  number-size player-missile 0
@define NUSIZ1  $05 ; ..111111  number-size player-missile 1
@define COLUP0  $06 ; 1111111.  color-lum player 0 and missile 0
@define COLUP1  $07 ; 1111111.  color-lum player 1 and missile 1
@define COLUPF  $08 ; 1111111.  color-lum playfield and ball
@define COLUBK  $09 ; 1111111.  color-lum background
@define CTRLPF  $0A ; ..11.111  control playfield ball size & collisions
@define REFP0   $0B ; ....1...  reflect player 0
@define REFP1   $0C ; ....1...  reflect player 1
@define PF0     $0D ; 1111....  playfield register byte 0
@define PF1     $0E ; 11111111  playfield register byte 1
@define PF2     $0F ; 11111111  playfield register byte 2
@define RESP0   $10 ; <strobe>  reset player 0
@define RESP1   $11 ; <strobe>  reset player 1
@define RESM0   $12 ; <strobe>  reset missile 0
@define RESM1   $13 ; <strobe>  reset missile 1
@define RESBL   $14 ; <strobe>  reset ball
@define AUDC0   $15 ; ....1111  audio control 0
@define AUDC1   $16 ; ....1111  audio control 1
@define AUDF0   $17 ; ...11111  audio frequency 0
@define AUDF1   $18 ; ...11111  audio frequency 1
@define AUDV0   $19 ; ....1111  audio volume 0
@define AUDV1   $1A ; ....1111  audio volume 1
@define GRP0    $1B ; 11111111  graphics player 0
@define GRP1    $1C ; 11111111  graphics player 1
@define ENAM0   $1D ; ......1.  graphics (enable) missile 0
@define ENAM1   $1E ; ......1.  graphics (enable) missile 1
@define ENABL   $1F ; ......1.  graphics (enable) ball
@define HMP0    $20 ; 1111....  horizontal motion player 0
@define HMP1    $21 ; 1111....  horizontal motion player 1
@define HMM0    $22 ; 1111....  horizontal motion missile 0
@define HMM1    $23 ; 1111....  horizontal motion missile 1
@define HMBL    $24 ; 1111....  horizontal motion ball
@define VDELP0  $25 ; .......1  vertical delay player 0
@define VDELP1  $26 ; .......1  vertical delay player 1
@define VDELBL  $27 ; .......1  vertical delay ball
@define RESMP0  $28 ; ......1.  reset missile 0 to player 0
@define RESMP1  $29 ; ......1.  reset missile 1 to player 1
@define HMOVE   $2A ; <strobe>  apply horizontal motion
@define HMCLR   $2B ; <strobe>  clear horizontal motion registers
@define CXCLR   $2C ; <strobe>  clear collision latches

; TIA - READ ADDRESS SUMMARY (Read only)
@define CXM0P   $30 ; 11......  read collision M0-P1, M0-P0 (Bit 7,6)
@define CXM1P   $31 ; 11......  read collision M1-P0, M1-P1
@define CXP0FB  $32 ; 11......  read collision P0-PF, P0-BL
@define CXP1FB  $33 ; 11......  read collision P1-PF, P1-BL
@define CXM0FB  $34 ; 11......  read collision M0-PF, M0-BL
@define CXM1FB  $35 ; 11......  read collision M1-PF, M1-BL
@define CXBLPF  $36 ; 1.......  read collision BL-PF, unused
@define CXPPMM  $37 ; 11......  read collision P0-P1, M0-M1
@define INPT0   $38 ; 1.......  read pot port
@define INPT1   $39 ; 1.......  read pot port
@define INPT2   $3A ; 1.......  read pot port
@define INPT3   $3B ; 1.......  read pot port
@define INPT4   $3C ; 1.......  read input
@define INPT5   $3D ; 1.......  read input

; PIA 6532 - RAM, Switches, and Timer (Read/Write)
@define SWCHA   $0280 ; 11111111  Port A; input or output  (read or write)
@define SWACNT  $0281 ; 11111111  Port A DDR, 0= input, 1=output
@define SWCHB   $0282 ; 11111111  Port B; console switches (read only)
@define SWBCNT  $0283 ; 11111111  Port B DDR (hardwired as input)
@define INTIM   $0284 ; 11111111  Timer output (read only)
@define INSTAT  $0285 ; 11......  Timer Status (read only, undocumented)
@define TIM1T   $0294 ; 11111111  set 1 clock interval (838 nsec/interval)
@define TIM8T   $0295 ; 11111111  set 8 clock interval (6.7 usec/interval)
@define TIM64T  $0296 ; 11111111  set 64 clock interval (53.6 usec/interval)
@define T1024T  $0297 ; 11111111  set 1024 clock interval (858.2 usec/interval)

@endif