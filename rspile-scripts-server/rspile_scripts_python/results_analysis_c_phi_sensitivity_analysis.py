import inspect
import io
import logging
import os

from RSPileScripting.enums import *
from RSPileScripting.RSPileModeler import RSPileModeler

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(lambda: None)))
RSPileModeler.startApplication(port=60044)

rspile_modeler = RSPileModeler(60044)

model = rspile_modeler.openFile(
    rf"{current_dir}\example_models\SoilStrengthAnalysis.rspile2"
)

soil_properties = model.getSoilProperties()
sand = soil_properties[0]
clay = soil_properties[1]

sand.setName("Sand")
clay.setName("Clay")

friction_angle = 35
sand.AxialProperties.setAxialType(AxialType.API_SAND)

undrained_shear_strength = 90
clay.AxialProperties.setAxialType(AxialType.API_CLAY)

pile_section_1 = model.getPileSections()[0]

pile_section_1.PileAnalysis.setSectionType(SectionType.ELASTIC)
pile_section_1.PileAnalysis.Elastic.setCrossSectionType(
    ElasticCrossSectionType.CIRCULAR
)
pile_section_1.PileAnalysis.Elastic.setYoungsModulus(32)

pile_type_1 = model.getPileTypes()[0]
pile_type_1.PileAnalysis.Sections.setPileSegmentsByLength(
    1, [[pile_section_1.getName(), 20]]
)

logger = logging.getLogger("Rocscience.RSPile._client")
log_stream = io.StringIO()
stream_handler = logging.StreamHandler(log_stream)
logger.addHandler(stream_handler)  # Attach the stream handler to capture logs
logger.setLevel(logging.WARNING)  # Ensure warnings are logged

non_convergence = False

while not non_convergence and friction_angle > 0 and undrained_shear_strength > 0:
    sand.AxialProperties.APISand.setFrictionAngle(friction_angle)
    clay.AxialProperties.APIClay.setUndrainedShearStrength(undrained_shear_strength)
    model.save()
    model.compute()

    # Get log warnings from the stream
    log_stream.seek(0)
    log_contents = log_stream.read()

    if "Convergence may not be achieved" in log_contents:
        non_convergence = True
        print(f"Friction Angle at failure: {friction_angle}")
        print(f"Undrained Shear Strength at failure: {undrained_shear_strength}")
        break  # Stop loop immediately if non-convergence warning is found

    friction_angle -= 0.5
    undrained_shear_strength -= 3

# Cleanup
logger.removeHandler(stream_handler)
log_stream.close()

model.save()
model.close()

rspile_modeler.closeApplication()
