#ifndef ad5761_h
#define ad5761_h

#include <SPI.h>

// Select GPIO pins for SPI
#define AD5761_MOSI_PIN  23
#define AD5761_CLK_PIN   18
#define csPin0           5  // GPIO5 as CS

// Define clock rate
#define AD5761_CLOCK_RATE 10000000 // 10 MHz for stability

void ad5761_init();
void ad5761_write(uint8_t reg_addr_cmd, uint16_t reg_data, char cs);

#endif