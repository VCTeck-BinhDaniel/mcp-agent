import inspect
import os

from RSPileScripting.enums import *
from RSPileScripting.RSPileModeler import RSPileModeler
from RSPileScripting.Utilities.ColorPicker import ColorPicker

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(lambda: None)))
RSPileModeler.startApplication(60044)

rspile_modeler = RSPileModeler(60044)
model = rspile_modeler.openFile(rf"{current_dir}\example_models\HelicalPile.rspile2")

pile_section_list = model.getPileSections()

pile_section1 = pile_section_list[0]

pile_section1.setName("Hollow Section")
pile_section1.setColor(ColorPicker.Lime)
pile_section1.HelicalCapacity.setCrossSectionType(HelicalCrossSectionType.SQUARE_HOLLOW)
pile_section1.HelicalCapacity.SquareHollow.setOuterSideLength(0.2)
pile_section1.HelicalCapacity.SquareHollow.setThickness(0.02)


print(pile_section1.getName())
print(ColorPicker.getColorName(pile_section1.getColor()))
print(pile_section1.HelicalCapacity.getCrossSectionType())
print(pile_section1.HelicalCapacity.SquareHollow.getOuterSideLength())
print(pile_section1.HelicalCapacity.SquareHollow.getThickness())

model.save()
model.close()

rspile_modeler.closeApplication()
