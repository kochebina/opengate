/* --------------------------------------------------
   Copyright (C): OpenGATE Collaboration
   This software is distributed under the terms
   of the GNU Lesser General  Public Licence (LGPL)
   See LICENSE.md for further details
   -------------------------------------------------- */

#ifndef GateChemistryActor_h
#define GateChemistryActor_h

#include "GateVActor.h"
#include <pybind11/stl.h>

class G4EmCalculator;

class GateChemistryActor : public GateVActor {

public:
  // Constructor
  GateChemistryActor(pybind11::dict &user_info);

  void NewStage() override;

};

#endif // GateLETActor_h
