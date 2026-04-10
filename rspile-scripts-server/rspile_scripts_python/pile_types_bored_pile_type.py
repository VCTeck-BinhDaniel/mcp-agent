import inspect
import os

from RSPileScripting.enums import *
from RSPileScripting.RSPileModeler import RSPileModeler
from RSPileScripting.Utilities.ColorPicker import ColorPicker

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(lambda: None)))
RSPileModeler.startApplication(60044)

rspile_modeler = RSPileModeler(60044)
model = rspile_modeler.openFile(rf"{current_dir}\example_models\BoredPile.rspile2")

pile_section_list = model.getPileTypes()

pile_type1 = pile_section_list[0]

pile_type1.setName("Circular Concrete Pile")
pile_type1.setColor(ColorPicker.Red)
pile_type1.Bored.Sections.setCrossSectionType(BoredPileTypeCrossSection.BELL)
pile_type1.Bored.Sections.setPileSegmentsByLength(1.2, [["Circular Section", 32]])

bell = pile_type1.Bored.Sections.Bell
bell.setLengthAboveBell(0.5)
bell.setAngle(45)
bell.setBaseThickness(0.2)
bell.setBaseDiameterDefinitionType(BaseDiamaterDefinitionType.VALUE)
bell.setBaseDiameter(3)

print(pile_type1.getName())
print(ColorPicker.getColorName(pile_type1.getColor()))
print(pile_type1.Bored.Sections.getCrossSectionType())
print(pile_type1.Bored.Sections.getPileSegmentsByLength())
print(pile_type1.Bored.Sections.Bell.getLengthAboveBell())
print(pile_type1.Bored.Sections.Bell.getAngle())
print(pile_type1.Bored.Sections.Bell.getBaseThickness())
print(pile_type1.Bored.Sections.Bell.getBaseDiameterDefinitionType())
print(pile_type1.Bored.Sections.Bell.getBaseDiameter())

model.save()
model.close()

rspile_modeler.closeApplication()
