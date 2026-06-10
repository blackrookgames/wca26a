@include "./common.asm"

?ENTRY LAB_f000
?BREAK LAB_f000

; Zero page
@define DAT_0000 $00
@define DAT_0001 $01
@define DAT_0002 $02
@define DAT_0008 $08
@define DAT_0009 $09
@define DAT_000e $0E
@define DAT_0080 $80

!OFFSET $F000

; Code beginning
; On the Atari 2600, cartridge ROM starts at $F000
LAB_f000:
    LDX #$00
    LDA #$00
LAB_f004:
    STA $00,X
    INX 
    BNE LAB_f004
    LDA #$00
    STA DAT_0080
    LDA #$45
    STA DAT_0008
    LDY #$00
LAB_f013:
    LDA #$00
    STA DAT_0001
    LDA #$02
    STA DAT_0000
    STA DAT_0002
    STA DAT_0002
    STA DAT_0002
    LDA #$00
    STA DAT_0000
    LDX #$00
LAB_f027:
    STA DAT_0002
    INX 
    CPX #$25
    BNE LAB_f027
    INY 
    CPY #$14
    BNE LAB_f037
    LDY #$00
    INC DAT_0080
LAB_f037:
    LDA DAT_0080
    STA DAT_000e
    LDX #$00
LAB_f03d:
    STX DAT_0009
    STA DAT_0002
    INX 
    CPX #$c0
    BNE LAB_f03d
    LDA #$42
    STA DAT_0001
    LDX #$00
LAB_f04c:
    STA DAT_0002
    INX 
    CPX #0x1e
    BNE LAB_f04c
    JMP LAB_f013