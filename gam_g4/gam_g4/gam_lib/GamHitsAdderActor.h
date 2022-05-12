/* --------------------------------------------------
   Copyright (C): OpenGATE Collaboration
   This software is distributed under the terms
   of the GNU Lesser General  Public Licence (LGPL)
   See LICENSE.md for further details
   -------------------------------------------------- */

#ifndef GamHitsAdderActor_h
#define GamHitsAdderActor_h

#include <pybind11/stl.h>
#include "G4Cache.hh"
#include "GamVActor.h"
#include "GamHitsCollection.h"
#include "GamTHitAttribute.h"
#include "GamHelpersHits.h"

namespace py = pybind11;

/*
 * Create a collection of "singles":
 *
 * - when every event ends, we consider all hits in the bottom most volume
 * - sum all deposited energy
 * - compute one single position, either the one the hit with the max energy (EnergyWinnerPosition)
 *   or the energy weighted position (EnergyWeightedCentroidPosition)
 *
 *  Warning: if the volume is composed of several sub volumes, hits will be
 *  grouped independently for all sub-volumes. This is determine thanks to the UniqueVolumeID.
 *
 *  Warning: hits are gathered per Event, not per time.
 *
 */

class GamHitsAdderInVolume;

class GamHitsAdderActor : public GamVActor {

public:

    enum AdderPolicy {
        Error, EnergyWinnerPosition, EnergyWeightedCentroidPosition
    };

    explicit GamHitsAdderActor(py::dict &user_info);

    ~GamHitsAdderActor() override;

    // Called when the simulation start (master thread only)
    void StartSimulationAction() override;

    // Called when the simulation end (master thread only)
    void EndSimulationAction() override;

    // Called every time a Run starts (all threads)
    void BeginOfRunAction(const G4Run *run) override;

    // Called every time a Run ends (all threads)
    void EndOfRunAction(const G4Run *run) override;

    void EndOfSimulationWorkerAction(const G4Run * /*unused*/) override;

    void EndOfEventAction_old(const G4Event *event);

    // Called every time an Event ends (all threads)
    void EndOfEventAction(const G4Event *event) override;

protected:
    std::string fOutputFilename;
    std::string fInputHitsCollectionName;
    std::string fOutputHitsCollectionName;
    GamHitsCollection *fOutputHitsCollection;
    GamHitsCollection *fInputHitsCollection;
    AdderPolicy fPolicy;
    std::vector<std::string> fUserSkipHitAttributeNames;
    double fEdepMin;
    double fEdepMax;

    void InitializeComputation();

    void AddHitPerVolume(size_t i);

    // During computation (thread local)
    struct threadLocalT {
        std::vector<double> *fInputEdep;
        std::vector<double> *fInputTime;
        std::vector<G4ThreeVector> *fInputPos;
        std::vector<GamUniqueVolumeID::Pointer> *fInputVolumeId;
        std::map<GamUniqueVolumeID::Pointer, GamHitsAdderInVolume> fMapOfHitsInVolume;
        GamHitsAttributesFiller *fHitsAttributeFiller;
        GamVHitAttribute *fOutputEdepAttribute;
        GamVHitAttribute *fOutputPosAttribute;
        GamVHitAttribute *fOutputGlobalTimeAttribute;
        size_t fIndex;
    };
    G4Cache<threadLocalT> fThreadLocalData;

};

#endif // GamHitsAdderActor_h
