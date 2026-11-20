# An Exploratory Urban Mobility Digital Twin for Huancayo with Traceable Data Hexagonal Services and Reproducible SUMO Scenarios

Carlos Leonardo Escobar Cárdenas, Brayan José Ochoa Segovia, Christian John Zevallos Meza, Fabricio Renzo Chicmana Víncula, and Marcelo Alen Morris Córdova
Universidad Continental, Huancayo, Peru

## Abstract

Urban mobility digital twins need trustworthy local observations and verified road geometry before they can support operational decisions. This paper reports an academic prototype for the Avenida Ferrocarril area in Huancayo that deliberately separates historical evidence, a national machine-learning experiment, and an exploratory local simulation. A React interface calls a FastAPI service organized around application ports and adapters; PostgreSQL/PostGIS persists project data. Nine municipal traffic-count records from 2013 provide historical local context. A distinct national toll-data experiment uses a temporal train–test split and a random-forest model; its error metrics are reported only for that dataset. For local exploration, a versioned OpenStreetMap extract was converted to a SUMO 1.28.0 network. Three deterministic synthetic-demand settings, generated with seed 30167, completed 113, 225, and 450 trips. Mean trip durations were 168.61, 182.52, and 192.16 seconds, respectively. A protected API can execute the normal scenario in staging, where the web interface displayed 225 of 225 completed trips. Source and route hashes, limitations, and executable checks make the prototype auditable. Neither current local counts nor certified corridor geometry were available. Accordingly, the simulation is a reproducible software experiment, not a calibrated representation or forecast of 2026 traffic.

**Keywords:** urban mobility; digital twin; Huancayo; OpenStreetMap; SUMO; hexagonal architecture; reproducibility.

## 1 Introduction

Traffic information relevant to one city corridor often comes from datasets with different locations, periods, and measurement methods. Combining those records in a single interface can be useful, but it creates a risk of presenting unrelated evidence as one current traffic estimate. The Huancayo project addresses this risk by exposing provenance alongside every dataset and by labelling its local simulation as exploratory.

The prototype has three successive minimum viable products (MVPs). MVP1 presents historical local counts and source-aware visualizations. MVP2 adds persistent storage, provenance, and reproducible experiment records. MVP3 introduces an OpenStreetMap (OSM) road network and three Simulation of Urban MObility (SUMO) runs. The research question here is narrow: can a web-based, modular prototype reproduce and communicate distinct traffic scenarios while preserving the limits of the underlying evidence?

The contribution is an implementation and evaluation of an auditable workflow: a versioned map extract, deterministic synthetic trips, checksums for derived assets, a protected execution endpoint, and a user interface that distinguishes precomputed comparisons from newly executed results. No claim is made that the current prototype estimates actual corridor flow.

## 2 Related Work

Rundel and De Amicis [1] connect digital-twin representations, SUMO traffic simulation, and visualization. Their study highlights the cost of detailed infrastructure for smaller municipalities. The present prototype similarly pursues an accessible workflow, but its browser map and service architecture are simpler than their 3D and virtual-reality system. Its local scenarios lack field validation.

Wibisana et al. [2] demonstrate a LiDAR-informed traffic monitoring and simulation workflow in Sofia, using observed trajectories and SUMO. Their method illustrates why high-quality observations matter for a traffic digital twin. The Huancayo prototype has no equivalent sensing campaign. It therefore treats OSM-derived geometry and generated trips as hypotheses for software exploration, never as measured trajectories.

These studies motivate a distinction between an operational digital twin synchronized with observations and a prototype that exposes data lineage and repeatable simulations. This paper evaluates the latter.

## 3 Materials and Methods

### 3.1 Evidence streams

The local historical stream contains nine count records from the Municipality of Huancayo for 2013, associated with P03, P04, and P42; the recorded counts sum to 11,892 vehicles across their documented periods [3]. They are not 2026 measurements. A separate national toll-unit dataset supplied the machine-learning experiment. Its reported metadata describe 8,946 training rows, 2,340 test rows, and a temporal split [4]. These national records do not describe Avenida Ferrocarril.

The exploratory spatial stream is an OSM snapshot from a bounding box approximately west −75.220, south −12.073, east −75.200, north −12.060 [5]. SUMO's network conversion produced 1,451 passenger-car edges, of which 59 carried the Avenida Ferrocarril name in the derived network. OSM is collaboratively maintained and is not certified municipal geometry.

### 3.2 Architecture

The frontend uses React 19, TypeScript, Vite, React Router, and Leaflet. FastAPI exposes public read routes and authenticated editor commands. The backend separates domain models, application use cases and ports, input/output adapters, and infrastructure configuration. A SQL adapter persists data through PostgreSQL/PostGIS. For the exploratory run, an application port abstracts the SUMO executor; a route calls a use case and receives the adapter's result. A fake port supports isolated unit testing. The interface shows the provenance and scientific limitations of each stream.

### 3.3 Scenario construction

The OSM extract and derived SUMO files are versioned with SHA-256 checksums [5]. Random trip generation used seed 30167 and departures over 900 seconds. The low, normal, and high settings used one synthetic departure every 8, 4, and 2 seconds, respectively; the simulator ran to 1,800 seconds. The report records route counts, arrivals, mean duration, waiting time, and trip speed. These values are computed over completed trips. Trip intervals are experimental inputs, not estimates from local counts.

### 3.4 Verification procedure

The archived report is reproducible through the repository's simulation script and contains hashes for map, network, and route files [5]. The web build and backend tests were run locally on 20 November 2026. An earlier published staging session displayed a newly calculated normal scenario after editor authentication, with 225 of 225 trips completed [6]. The published screenshot is an interface observation; the authenticated raw API response was not independently archived in that session. Twelve PostgreSQL-dependent local tests were skipped because the optional database fixture was unavailable on the testing machine.

## 4 Implementation

MVP1 implemented historical traffic consultation and source-aware views. MVP2 added SQL-backed persistence, dataset provenance, and recorded model experiments. MVP3 added versioned OSM/SUMO assets, a comparison screen, and an authenticated command to rerun one of three allowed demand levels. This sequence is documented by user stories HU-01 to HU-18 in the project report [3]. A public Scrum-Kanban board with sprint velocity or burndown measurements was not available for verification; no such metrics are reported.

The execution endpoint accepts only the predefined demand levels. The server verifies the input assets, limits concurrent runs, applies a timeout, and returns the simulator's result through the application port. The web interface displays the newly calculated result beside its source label. Public report retrieval remains separate from the editor command. The repository contains the source code, deployment blueprint, and reproduction instructions [5].

## 5 Results

| Synthetic demand | Departure interval | Completed trips | Mean duration (s) | Mean waiting (s) | Mean trip speed (km/h) |
| --- | ---: | ---: | ---: | ---: | ---: |
| Low | 8 s | 113/113 | 168.61 | 34.27 | 36.34 |
| Normal | 4 s | 225/225 | 182.52 | 42.89 | 34.37 |
| High | 2 s | 450/450 | 192.16 | 46.67 | 33.64 |

All generated trips completed in the three archived runs. Within this fixed network and route-generation method, higher synthetic departure intensity coincided with longer mean duration and waiting time and lower mean speed. The difference between high and low demand was 23.55 seconds in mean duration and 12.40 seconds in mean waiting time. This is an internal experimental comparison; no confidence interval or local prediction accuracy is inferred.

The independent national random-forest experiment reports MAE 7,083.46, RMSE 17,657.61, and R² 0.982168 over its temporal test set [4]. A naive baseline in the metadata has MAE 8,309.34. The target unit and national toll-unit context determine the meaning of those errors; they are not errors for the Huancayo corridor and are not compared numerically with SUMO trip durations.

Local quality checks on 20 November 2026 completed 83 backend tests, with 12 PostgreSQL-dependent tests skipped. The frontend passed its TypeScript and architecture check and compiled successfully. A separate live Render observation showed the normal SUMO run and the four displayed scenario metrics [6]. These checks establish working software paths, not uninterrupted availability, cybersecurity assurance, or traffic validity.

## 6 Discussion

The prototype makes three kinds of evidence visible without silently joining them: historical municipal counts, a national ML evaluation, and a local synthetic road-network experiment. This separation is essential because all three have different populations and time frames. The OSM/SUMO outputs reveal how the current software responds to configured demand, but neither the input flow nor geometry has been validated against 2026 Avenida Ferrocarril observations.

The architecture supports replacement of the SUMO executor through a port without changing the HTTP contract. That is a software-maintenance benefit, not evidence of model accuracy. The editor authentication restricts simulation commands, while public reads allow inspection of sources and results. Remaining engineering work includes a complete dependency vulnerability scan, database-enabled tests in this environment, request-rate controls, and representative load testing.

The main scientific limitation is the absence of dated local counts with verified locations and official usable geometry. A future calibration campaign should define count locations and intervals, audit geometry and traffic controls, partition observations into calibration and validation sets, and report error against observed values. Until then, the system should retain its “exploratory, uncalibrated” label. No emissions or social-benefit estimates are made from these scenarios.

## 7 Conclusion

A web-based mobility prototype for Huancayo can present heterogeneous sources, persist state, and rerun three deterministic OSM/SUMO scenarios while preserving their provenance. The normal staging scenario displayed 225 completed trips; the archived low and high scenarios completed 113 and 450 trips. These are reproducible synthetic results. The project demonstrates an auditable software architecture and scenario workflow, with current traffic estimation and calibrated decision support remaining outside its verified scope.

## References

[1] Samuel Rundel and Raffaele De Amicis. 2023. Leveraging digital twin and game-engine for traffic simulations and visualizations. *Frontiers in Virtual Reality* 4, 1048753. https://doi.org/10.3389/frvir.2023.1048753

[2] Maulana Ikram Wibisana, Mila Koeva, Pirouz Nourian, Dessislava Petrova-Antonova, and Kaloyan Karamitov. 2024. A LiDAR-Based Digital Twinning Workflow for Traffic Monitoring and Simulation. *ISPRS Annals of the Photogrammetry, Remote Sensing and Spatial Information Sciences* X-4-2024, 411–418. https://doi.org/10.5194/isprs-annals-X-4-2024-411-2024

[3] Gemelo Digital Huancayo team. 2026. *Informe de Proyecto y Software: PMV1, PMV2 y PMV3*. `docs/informes/Informe_PMV1_PMV2_PMV3_2026-11-13.docx`.

[4] Gemelo Digital Huancayo team. 2026. National toll-data model metadata. `ml/models/demo_peru/metadata_mtc_toll_demo.json`.

[5] Gemelo Digital Huancayo team. 2026. Exploratory OSM/SUMO simulation report and reproduction guide. `frontend/src/data/osm-exploratory-report.json`; `simulation/README.md`.

[6] Gemelo Digital Huancayo team. 2026. Staging integration evidence, 18 November. `docs/evidencias/2026-11-18/README.md`.

[7] OpenStreetMap contributors. 2026. Copyright and License. https://www.openstreetmap.org/copyright

[8] Eclipse SUMO. 2026. OpenStreetMap import and trip-generation documentation. https://sumo.dlr.de/docs/Networks/Import/OpenStreetMap.html ; https://sumo.dlr.de/docs/Tools/Trip.html
