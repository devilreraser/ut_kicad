import os
import csv
import shutil
import pcbnew
from collections import defaultdict
from .config import *


class ProcessManager:
    def __init__(self):
        self.board = pcbnew.GetBoard()
        self.bom = []
        self.components = []

    def generate_gerber(self, temp_dir):
        settings = self.board.GetDesignSettings()
        settings.m_SolderMaskMargin = 0
        settings.m_SolderMaskMinWidth = 0

        plot_controller = pcbnew.PLOT_CONTROLLER(self.board)

        plot_options = plot_controller.GetPlotOptions()
        plot_options.SetOutputDirectory(temp_dir)
        plot_options.SetPlotFrameRef(False)
        plot_options.SetSketchPadLineWidth(pcbnew.FromMM(0.1))
        plot_options.SetAutoScale(False)
        plot_options.SetScale(1)
        plot_options.SetMirror(False)
        plot_options.SetUseGerberAttributes(True)
        plot_options.SetExcludeEdgeLayer(True)
        plot_options.SetUseGerberProtelExtensions(False)
        plot_options.SetUseAuxOrigin(True)
        plot_options.SetSubtractMaskFromSilk(False)
        plot_options.SetDrillMarksType(0)  # NO_DRILL_SHAPE

        for layer_info in plotPlan:
            if self.board.IsLayerEnabled(layer_info[1]):
                plot_controller.SetLayer(layer_info[1])
                plot_controller.OpenPlotfile(
                    layer_info[0],
                    pcbnew.PLOT_FORMAT_GERBER,
                    layer_info[2])
                plot_controller.PlotLayer()

        plot_controller.ClosePlot()

    def generate_drills(self, temp_dir):
        drill_writer = pcbnew.EXCELLON_WRITER(self.board)

        drill_writer.SetOptions(
            False,
            True,
            self.board.GetDesignSettings().GetAuxOrigin(),
            False)
        drill_writer.SetFormat(False)
        drill_writer.CreateDrillandMapFilesSet(temp_dir, True, False)

    def generate_netlist(self, temp_dir):
        netlist_writer = pcbnew.IPC356D_WRITER(self.board)
        netlist_writer.Write(os.path.join(temp_dir, netlistFileName))

    def generate_positions(self, temp_dir):
        if hasattr(self.board, 'GetModules'):
            footprints = list(self.board.GetModules())
        else:
            footprints = list(self.board.GetFootprints())

        # sort footprint after designator
        footprints.sort(key=lambda x: x.GetReference())

        # unique designator dictionary
        footprint_designators = defaultdict(int)
        for i, footprint in enumerate(footprints):
            # count unique designators
            footprint_designators[footprint.GetReference()] += 1
        bom_designators = footprint_designators.copy()

        with open((os.path.join(temp_dir, designatorsFileName)), 'w', encoding='utf-8') as f:
            for key, value in footprint_designators.items():
                f.write('%s:%s\n' % (key, value))

        for i, footprint in enumerate(footprints):
            try:
                footprint_name = str(footprint.GetFPID().GetFootprintName())
            except AttributeError:
                footprint_name = str(footprint.GetFPID().GetLibItemName())

            layer = {
                pcbnew.F_Cu: 'top',
                pcbnew.B_Cu: 'bottom',
            }.get(footprint.GetLayer())

            # mount_type = {
            #     0: 'smt',
            #     1: 'tht',
            #     2: 'smt'
            # }.get(footprint.GetAttributes())

            if not footprint.GetAttributes() & pcbnew.FP_EXCLUDE_FROM_POS_FILES:
                # append unique ID if duplicate footprint designator
                unique_id = ""
                if footprint_designators[footprint.GetReference()] > 1:
                    unique_id = str(footprint_designators[footprint.GetReference()])
                    footprint_designators[footprint.GetReference()] -= 1

                orientation_fix = footprint.GetOrientation() / 10.0


                part_number = self._getMpnFromFootprint(footprint)

                # footprint_name_string = footprint.GetFootprintName()

                #one zoom mouse is 1.5 coef

                position_x = footprint.GetPosition()[0]
                position_y = footprint.GetPosition()[1]

                # AQG22212
                if part_number == "C719647":

                    if orientation_fix == 90:
                        position_x += 15240000
                        position_y += -0
                    elif orientation_fix == -90:
                        position_x -= 15240000
                        position_y -= -0
                    elif orientation_fix == 0:
                        position_y -= -15240000
                        position_x += 0
                    elif orientation_fix == 180:
                        position_y += -15240000
                        position_x -= 0

                    orientation_fix -= 270
                    if orientation_fix < -90:
                        orientation_fix += 360
                # ESP32
                elif footprint_name == "ESP32-WROOM-32":

                    if orientation_fix == 90:
                        position_x += 783650
                    elif orientation_fix == -90:
                        position_x -= 783650
                    elif orientation_fix == 0:
                        position_y -= -783650
                    elif orientation_fix == 180:
                        position_y += -783650

                    orientation_fix -= 90
                    if orientation_fix < -90:
                        orientation_fix += 360
                # 3-pin 5.08
                elif part_number == "C409143":

                    if orientation_fix == 90:
                        position_y += -5080000
                    elif orientation_fix == -90:
                        position_y -= -5080000
                    elif orientation_fix == 0:
                        position_x += 5080000
                    elif orientation_fix == 180:
                        position_x -= 5080000

                    orientation_fix -= 0
                    if orientation_fix < -90:
                        orientation_fix += 360
                # 2-pin 5.08      
                elif part_number == "C441386":

                    if orientation_fix == 90:
                        position_y += -2540000
                        position_x -= 50000
                    elif orientation_fix == -90:
                        position_y -= -2540000
                        position_x += 50000
                    elif orientation_fix == 0:
                        position_x += 2540000
                        position_y += -50000
                    elif orientation_fix == 180:
                        position_x -= 2540000
                        position_y -= -50000

                    orientation_fix -= 180
                    if orientation_fix < -90:
                        orientation_fix += 360
                # 3-pin 3.81       
                elif part_number == "C395692":

                    if orientation_fix == 90:
                        position_y += -3810000
                    elif orientation_fix == -90:
                        position_y -= -3810000
                    elif orientation_fix == 0:
                        position_x += 3810000
                    elif orientation_fix == 180:
                        position_x -= 3810000

                    orientation_fix -= 180
                    if orientation_fix < -90:
                        orientation_fix += 360
                # 2-pin 3.81    
                elif part_number == "C8396":

                    if orientation_fix == 90:
                        position_y += -1905000
                    elif orientation_fix == -90:
                        position_y -= -1905000
                    elif orientation_fix == 0:
                        position_x += 1905000
                    elif orientation_fix == 180:
                        position_x -= 1905000

                    orientation_fix -= 180
                    if orientation_fix < -90:
                        orientation_fix += 360
                    
                elif footprint_name == "C_Rect_L10.0mm_W4.0mm_P7.50mm_FKS3_FKP3":

                    if orientation_fix == 90:
                        position_y += -3750000
                    elif orientation_fix == -90:
                        position_y -= -3750000
                    elif orientation_fix == 0:
                        position_x += 3750000
                    elif orientation_fix == 180:
                        position_x -= 3750000

                    orientation_fix -= 0
                    if orientation_fix < -90:
                        orientation_fix += 360

                elif footprint_name == "R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal":

                    if orientation_fix == 90:
                        position_y += -5080000
                    elif orientation_fix == -90:
                        position_y -= -5080000
                    elif orientation_fix == 0:
                        position_x += 5080000
                    elif orientation_fix == 180:
                        position_x -= 5080000

                    orientation_fix -= 0
                    if orientation_fix < -90:
                        orientation_fix += 360

                elif footprint_name == "R_Axial_DIN0204_L3.6mm_D1.6mm_P7.62mm_Horizontal":

                    if orientation_fix == 90:
                        position_y += -3810000
                    elif orientation_fix == -90:
                        position_y -= -3810000
                    elif orientation_fix == 0:
                        position_x += 3810000
                    elif orientation_fix == 180:
                        position_x -= 3810000

                    orientation_fix -= 0
                    if orientation_fix < -90:
                        orientation_fix += 360

                elif footprint_name == "TO-220-3_Vertical":

                    if orientation_fix == 90:
                        position_y += -2540000
                    elif orientation_fix == -90:
                        position_y -= -2540000
                    elif orientation_fix == 0:
                        position_x += 2540000
                    elif orientation_fix == 180:
                        position_x -= 2540000

                    orientation_fix -= 0
                    if orientation_fix < -90:
                        orientation_fix += 360

                elif footprint_name == "SOT-89-3":
                    # one arrow click is 0.625 mm ?
                    if orientation_fix == 90:
                        position_y -= -285000
                    elif orientation_fix == -90:
                        position_y += -285000
                    elif orientation_fix == 0:
                        position_x -= 285000
                    elif orientation_fix == 180:
                        position_x += 285000

                    orientation_fix -= 180
                    if orientation_fix < -90:
                        orientation_fix += 360

                elif footprint_name == "TO-252-2":

                    if orientation_fix == 90:
                        position_y -= -1000000
                    elif orientation_fix == -90:
                        position_y += -1000000
                    elif orientation_fix == 0:
                        position_x -= 1000000
                    elif orientation_fix == 180:
                        position_x += 1000000

                    orientation_fix -= 0
                    if orientation_fix < -90:
                        orientation_fix += 360

                elif part_number == "C106900":
                    orientation_fix -= 0
                elif footprint.GetReference()[0] == 'U':
                    orientation_fix -= 90
                elif footprint.GetReference()[0] == 'Q':
                    orientation_fix -= 180
                else:
                    orientation_fix -= 0

                if orientation_fix < -90:
                    orientation_fix += 360


                self.components.append({
                    'Designator': "{}{}{}".format(footprint.GetReference(), "" if unique_id == "" else "_", unique_id),
                    'Mid X': (position_x - self.board.GetDesignSettings().GetAuxOrigin()[0]) / 1000000.0,
                    'Mid Y': (position_y - self.board.GetDesignSettings().GetAuxOrigin()[1]) * -1.0 / 1000000.0,
                    'Rotation': orientation_fix,
                    'Layer': layer,
                })

            if not footprint.GetAttributes() & pcbnew.FP_EXCLUDE_FROM_BOM:
                # append unique ID if we are dealing with duplicate bom designator
                unique_id = ""
                if bom_designators[footprint.GetReference()] > 1:
                    unique_id = str(bom_designators[footprint.GetReference()])
                    bom_designators[footprint.GetReference()] -= 1

                # merge similar parts into single entry
                insert = True
                # for component in self.bom:
                #     if component['Footprint'].upper() == footprint_name.upper() and component['Value'].upper() == footprint.GetValue().upper():
                #         component['Designator'] += ", " + "{}{}{}".format(footprint.GetReference(), "" if unique_id == "" else "_", unique_id)
                #         component['Quantity'] += 1
                #         insert = False

                # add component to BOM
                if insert:
                    self.bom.append({
                        'Designator': "{}{}{}".format(footprint.GetReference(), "" if unique_id == "" else "_", unique_id),
                        'Footprint': footprint_name,
                        'Quantity': 1,
                        'Value': footprint.GetValue(),
                        # 'Mount': mount_type,
                        'LCSC Part #': self._getMpnFromFootprint(footprint),
                    })

        with open((os.path.join(temp_dir, placementFileName)), 'w', newline='', encoding='utf-8') as outfile:
            csv_writer = csv.writer(outfile)
            # writing headers of CSV file
            csv_writer.writerow(self.components[0].keys())

            for component in self.components:
                # writing data of CSV file
                if ('**' not in component['Designator']):
                    csv_writer.writerow(component.values())

    def generate_bom(self, temp_dir):

        with open((os.path.join(temp_dir, bomFileName)), 'w', newline='', encoding='utf-8') as outfile:
            csv_writer = csv.writer(outfile)
            # writing headers of CSV file
            csv_writer.writerow(self.bom[0].keys())

            # Output all of the component information
            for component in self.bom:
                # writing data of CSV file
                if ('**' not in component['Designator']):
                    csv_writer.writerow(component.values())

    def generate_archive(self, temp_dir, temp_file):
        temp_file = shutil.make_archive(temp_file, 'zip', temp_dir)
        temp_file = shutil.move(temp_file, temp_dir)

        # remove non essential files
        for item in os.listdir(temp_dir):
            if not item.endswith(".zip") and not item.endswith(".csv") and not item.endswith(".ipc"):
                os.remove(os.path.join(temp_dir, item))

        return temp_file

    def _getMpnFromFootprint(self, footprint):
        keys = ['mpn', 'Mpn', 'MPN', 'JLC_MPN', 'LCSC_MPN', 'LCSC Part #', 'JLC', 'LCSC']
        for key in keys:
            if footprint.HasProperty(key):
                return footprint.GetProperty(key)
