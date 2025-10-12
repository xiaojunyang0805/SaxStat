#ifndef REGISTER_H
#define REGISTER_H

/* Input Shift Register Commands for AD57X1 */
#define CMD_NOP                 0x0
#define CMD_WR_TO_INPUT_REG     0x1
#define CMD_UPDATE_DAC_REG      0x2
#define CMD_WR_UPDATE_DAC_REG   0x3
#define CMD_WR_CTRL_REG         0x4
#define CMD_SW_DATA_RESET       0x7
#define CMD_DIS_DAISY_CHAIN     0x9
#define CMD_RD_INPUT_REG        0xA
#define CMD_RD_DAC_REG          0xB
#define CMD_RD_CTRL_REG         0xC
#define CMD_SW_FULL_RESET       0xF

// Control Register Settings
#define CONTROL_REG_VAL 0b0000000001001000

#endif