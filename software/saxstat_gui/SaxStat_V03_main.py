import sys
from PyQt5.QtWidgets import QApplication
from gui_setup import CyclicVoltammetryGUI
from serial_comm import configure_serial, disconnect_serial, toggle_connection, refresh_com_ports, set_mode
from data_processing import get_cv_parameters, calibrate_offset, calculate_voltage_ramp, start_acquisition, stop_acquisition, read_serial_data, update_data, save_data
from plotting import initialize_plots, update_plots, update_graph_sizes

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = CyclicVoltammetryGUI()
    initialize_plots(gui)  # Call the function directly with gui as argument
    update_graph_sizes(gui)  # Set initial graph sizes
    gui.show()
    sys.exit(app.exec_())