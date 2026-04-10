import inspect
import os

from RSPileScripting.enums import *
from RSPileScripting.RSPileModeler import RSPileModeler
from RSPileScripting.Utilities.ColorPicker import ColorPicker

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(lambda: None)))
RSPileModeler.startApplication(60044)

rspile_modeler = RSPileModeler(60044)
model = rspile_modeler.openFile(rf"{current_dir}\example_models\BoredPile.rspile2")

pile_section_list = model.getPileSections()

pile_section1 = pile_section_list[0]

pile_section1.setName("Circular Section")
pile_section1.setColor(ColorPicker.Light_Grey)
pile_section1.BoredCapacity.setConcreteCylinderStrength(100)
pile_section1.BoredCapacity.setCrossSectionType(BoredCrossSectionType.CIRCULAR)
pile_section1.BoredCapacity.Circular.setDiameter(1.2)

print(pile_section1.getName())
print(ColorPicker.getColorName(pile_section1.getColor()))
print(pile_section1.BoredCapacity.getCrossSectionType())
print(pile_section1.BoredCapacity.Circular.getDiameter())

model.save()
model.close()

rspile_modeler.closeApplication()
