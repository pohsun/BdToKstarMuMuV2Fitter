#!/usr/bin/env make

CC=g++
CC_FLAGS=-lgfortran
ROOT_CFLAGS=$(shell root-config --cflags)
ROOT_LIBS  =$(shell root-config --glibs)
EVTGEN_FLAGS=-I${HOME}/local/EvtGen130/EvtGen/evtgen -L${HOME}/local/EvtGen130/EvtGen/evtgen/lib -lEvtGen -lEvtGenExternal
HEPMC_FLAGS =-I${HOME}/local/EvtGen130/EvtGen/external/HepMC/include      -L${HOME}/local/EvtGen130/EvtGen/external/HepMC/lib -lHepMC
PYTHIA_FLAGS=-I${HOME}/local/EvtGen130/EvtGen/external/pythia8180/include -L${HOME}/local/EvtGen130/EvtGen/external/pythia8180/lib -lpythia8 -llhapdfdummy
PHOTOS_FLAGS=-I${HOME}/local/EvtGen130/EvtGen/external/PHOTOS/include     -L${HOME}/local/EvtGen130/EvtGen/external/PHOTOS/lib -lPhotosCxxInterface -lPhotosFortran 
TAUOLA_FLAGS=-I${HOME}/local/EvtGen130/EvtGen/external/TAUOLA/include     -L${HOME}/local/EvtGen130/EvtGen/external/TAUOLA/lib -lTauolaCxxInterface -lTauolaFortran 
EVTGENEXTERNAL_FLAGS=$(HEPMC_FLAGS) $(PHOTOS_FLAGS) $(TAUOLA_FLAGS) $(PYTHIA_FLAGS)

default: evtgen130_btokstarmumu

evtgen130_btokstarmumu: evtgen130_btokstarmumu.cc
	$(CC) $(CC_FLAGS) $(ROOT_CFLAGS) -D EVTGEN_EXTERNAL evtgen130_btokstarmumu.cc -o $@ $(EVTGENEXTERNAL_FLAGS) $(EVTGEN_FLAGS) $(ROOT_LIBS)

clean:
	rm evtgen130_btokstarmumu
