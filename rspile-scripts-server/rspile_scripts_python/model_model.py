import inspect
import os

from RSPileScripting.enums import *
from RSPileScripting.RSPileModeler import RSPileModeler
from RSPileScripting.Utilities.ColorPicker import ColorPicker

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(lambda: None)))
RSPileModeler.startApplication(60044)

rspile_modeler = RSPileModeler(60044)
model = rspile_modeler.openFile(rf"{current_dir}\example_models\ExampleModel.rspile2")

soil_property = model.getSoilProperties()[0]
pile_section = model.getPileSections()[0]
pile_type = model.getPileTypes()[0]

soil_property.setName("Silty Sand")
pile_section.setName("Concrete Pile")
pile_type.setName("Pile Type 1A")

model.save()

soil_property.setColor(ColorPicker.Gold)
pile_section.setColor(ColorPicker.Indigo)
pile_type.setColor(ColorPicker.Light_Blue)

model.save(rf"{current_dir}\example_models\ExampleModelSaveAs.rspile2")
model.compute()
model.close()

rspile_modeler.closeApplication()
