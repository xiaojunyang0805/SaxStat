from pyqtgraph import PlotWidget

def update_graph_sizes(self):
    right_width = self.right_panel.width()
    right_height = self.right_panel.height()
    square_size = min(right_width // 2, right_height, 700)
    square_size = max(500, square_size)
    self.voltage_time_widget.setMinimumSize(square_size, square_size)
    self.voltage_time_widget.setMaximumSize(square_size, square_size)
    self.plot_widget.setMinimumSize(square_size, square_size)
    self.plot_widget.setMaximumSize(square_size, square_size)
    self.right_layout.setStretchFactor(self.voltage_time_widget, 1)
    self.right_layout.setStretchFactor(self.plot_widget, 1)

def update_plots(self):
    with self.lock:
        if self.applied_voltage_buffer and self.current_buffer:
            if len(self.applied_voltage_buffer) != len(self.current_buffer):
                print("Buffer length mismatch in CV plot")
                return
            self.plot_data.setData(self.applied_voltage_buffer, self.current_buffer)
            if self.applied_voltage_buffer:
                self.plot_widget.setXRange(min(self.applied_voltage_buffer), max(self.applied_voltage_buffer))
            if self.current_buffer:
                self.plot_widget.setYRange(min(self.current_buffer) - 10, max(self.current_buffer) + 10)

        if self.time_buffer and self.applied_voltage_buffer:
            if len(self.time_buffer) != len(self.applied_voltage_buffer):
                print("Buffer length mismatch in voltage-time plot")
                return
            self.voltage_time_data.setData(self.time_buffer, self.applied_voltage_buffer)
            if self.time_buffer:
                self.voltage_time_widget.setXRange(min(self.time_buffer), max(self.time_buffer))
            if self.applied_voltage_buffer:
                self.voltage_time_widget.setYRange(min(self.applied_voltage_buffer) - 0.1, max(self.applied_voltage_buffer) + 0.1)

def initialize_plots(self):
    self.voltage_time_widget = PlotWidget()
    self.right_layout.addWidget(self.voltage_time_widget)
    self.voltage_time_widget.setLabel('left', 'Applied Voltage (V)')
    self.voltage_time_widget.setLabel('bottom', 'Time (s)')
    self.voltage_time_widget.showGrid(x=True, y=True)
    self.voltage_time_widget.setTitle("Applied Voltage vs. Time")
    self.voltage_time_widget.setBackground('w')
    self.voltage_time_data = self.voltage_time_widget.plot(pen="r")

    self.plot_widget = PlotWidget()
    self.right_layout.addWidget(self.plot_widget)
    self.plot_widget.setLabel('left', 'Current')
    self.plot_widget.setLabel('bottom', 'Applied Voltage (V)')
    self.plot_widget.showGrid(x=True, y=True)
    self.plot_widget.setTitle("Cyclic Voltammetry")
    self.plot_widget.setBackground('w')
    self.plot_data = self.plot_widget.plot(pen="b")