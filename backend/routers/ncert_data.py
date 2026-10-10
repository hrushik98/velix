from typing import List, Dict, Any

NCERT_CURRICULUM = [
    {
        "id": "c8-sci-photo",
        "grade": "Class 8",
        "subject": "Science",
        "chapter_num": 1,
        "title": "Crop Production and Management",
        "age_group": "13-14 years",
        "sample_outline": [
            "Agricultural Practices & Soil Preparation",
            "Sowing and Adding Manure vs Fertilizers",
            "Irrigation Methods: Traditional vs Modern Drip",
            "Protection from Weeds & Harvesting",
            "Storage of Food Grains and Animal Husbandry"
        ],
        "default_context": "Crop production begins with soil preparation including ploughing and levelling. Good quality seeds are selected and sowed using seed drills. Nutrients are replenished using organic manure or chemical fertilizers like NPK. Irrigation methods have evolved from traditional moat and rahat to modern water-saving drip and sprinkler systems. Weeding ensures crops get maximum nutrients without competition. After maturity, harvesting is done mechanically, followed by threshing and safe storage in silos to prevent moisture and pest damage."
    },
    {
        "id": "c9-sci-matter",
        "grade": "Class 9",
        "subject": "Science",
        "chapter_num": 1,
        "title": "Matter in Our Surroundings",
        "age_group": "14-15 years",
        "sample_outline": [
            "Physical Nature of Matter & Particle Characteristics",
            "States of Matter: Solids, Liquids, and Gases",
            "Can Matter Change Its State? Temperature & Pressure",
            "Evaporation and Factors Affecting Evaporation",
            "Latent Heat of Fusion and Vaporization"
        ],
        "default_context": "Matter is made of particles that possess kinetic energy, have spaces between them, and attract each other. Solids have rigid shape and definite volume; liquids have indefinite shape but fixed volume; gases possess neither fixed shape nor fixed volume and have maximum compressibility. State changes occur via temperature changes (melting point, boiling point) and pressure changes. Latent heat is the heat energy absorbed or released during a phase change without change in temperature. Evaporation occurs at the surface below boiling point and causes cooling."
    },
    {
        "id": "c10-sci-light",
        "grade": "Class 10",
        "subject": "Science",
        "chapter_num": 10,
        "title": "Light: Reflection and Refraction",
        "age_group": "15-16 years",
        "sample_outline": [
            "Laws of Reflection & Spherical Mirrors",
            "Image Formation by Concave and Convex Mirrors",
            "Mirror Formula and Magnification",
            "Refraction of Light & Snell's Law",
            "Refractive Index and Lens Formula"
        ],
        "default_context": "Light travels in straight lines and reflects according to the laws of reflection: angle of incidence equals angle of reflection. Spherical mirrors are either concave (converging) or convex (diverging). Ray diagrams determine image characteristics: real/inverted or virtual/erect. The mirror formula relates focal length f, image distance v, and object distance u: 1/f = 1/v + 1/u. Refraction occurs when light passes between optical media with different refractive indices. Snell's law states sin(i)/sin(r) = constant. Lenses focus light through refraction."
    },
    {
        "id": "c10-hist-nation",
        "grade": "Class 10",
        "subject": "Social Science",
        "chapter_num": 1,
        "title": "The Rise of Nationalism in Europe",
        "age_group": "15-16 years",
        "sample_outline": [
            "The French Revolution and the Idea of the Nation",
            "The Making of Nationalism in Europe & Liberalism",
            "The Age of Revolutions: 1830-1848",
            "The Unification of Germany and Italy",
            "Visualising the Nation & Allegories (Marianne & Germania)"
        ],
        "default_context": "Nationalism emerged in nineteenth-century Europe as a force that transformed multi-national dynastic empires into nation-states. The French Revolution of 1789 introduced ideas of 'la patrie' (fatherland) and 'le citoyen' (citizen), along with a tricolour flag and centralized administration. The Napoleonic Code standardized laws and abolished feudalism. Liberal nationalism championed individual freedom and equality before the law. Otto von Bismarck orchestrated German unification through Prussian military power, while Cavour and Garibaldi united Italy."
    },
    {
        "id": "c7-sci-heat",
        "grade": "Class 7",
        "subject": "Science",
        "chapter_num": 4,
        "title": "Heat and Temperature",
        "age_group": "12-13 years",
        "sample_outline": [
            "Hot and Cold: Measuring Temperature",
            "Clinical vs Laboratory Thermometers",
            "Transfer of Heat: Conduction in Solids",
            "Convection in Liquids and Gases (Sea Breeze & Land Breeze)",
            "Radiation: Heat Transfer Without a Medium"
        ],
        "default_context": "Heat is a form of energy that flows from a body at a higher temperature to one at a lower temperature. Temperature is a measure of the degree of hotness of an object, measured in degrees Celsius using thermometers. Conduction transfers heat through direct particle contact without gross movement of matter. Convection transfers heat through bulk movement of fluids, driving phenomena like coastal sea breezes and land breezes. Radiation transfers thermal energy across empty space via electromagnetic waves without any medium."
    },
    {
        "id": "c6-sci-food",
        "grade": "Class 6",
        "subject": "Science",
        "chapter_num": 2,
        "title": "Components of Food & Nutrients",
        "age_group": "11-12 years",
        "sample_outline": [
            "Major Nutrients: Carbohydrates, Fats, and Proteins",
            "Vitamins and Minerals: Functions and Sources",
            "Dietary Fibres (Roughage) and Water",
            "What is a Balanced Diet?",
            "Deficiency Diseases: Scurvy, Rickets, and Anemia"
        ],
        "default_context": "Foods contain nutrients essential for growth, energy, and body maintenance. Carbohydrates and fats are energy-giving foods; proteins are bodybuilding foods needed for tissue repair. Vitamins protect our bodies against diseases, while minerals like calcium, iron, and iodine are needed in small amounts for specific functions. Dietary fibre helps get rid of undigested food. A balanced diet contains adequate proportions of all required nutrients. Deficiency of specific vitamins or minerals over long periods leads to deficiency diseases like scurvy, rickets, goitre, and anemia."
    }
]

GRADE_OPTIONS = [f"Class {i}" for i in range(1, 13)]

AGE_GROUPS = [
    "6-7 years", "7-8 years", "8-9 years", "9-10 years",
    "10-11 years", "11-12 years", "12-13 years", "13-14 years",
    "14-15 years", "15-16 years", "16-17 years", "17-18 years"
]
