#!/usr/bin/env python

from __future__ import print_function

import ROOT
from v2Fitter.Selector.SelectorCore import SelectorCore
import SingleBuToKstarMuMuSelector.cpp

from copy import copy

class StdSelector(SelectorCore):
    @classmethod
    def templateConfig(cls):
        cfg = SelectorCore.templateConfig()
        cfg.update({
            'datasetTag': "",
            'isMC': False,
            'cutSet': "default",
            'eventContent': "data"
        })
        return cfg

    # TODO: Make use of friend tree
    def _runSelectSteps(self):
        self.tree = ROOT.TChain(self.cfg['itreeName'])
        for tr in self.cfg['ifile']:
            self.tree.Add(tr)
        option = "cutSet={cutSet};eventContent={eventContent};isMC={isMC};".format(
                cutSet=self.cfg['cutSet'],
                eventContent=self.cfg['eventContent'],
                isMC="true" if self.cfg['isMC'] else "false",
            )
        if self.cfg['ofilename'] is None:
            self.cfg['ofilename'] = "ofilename=sel_{tag}_{eventContent}".format(
                tag=self.cfg['datasetTag'],
                eventContent=self.cfg['eventContent'])
            if self.cfg['oIsFriend']:
                self.cfg['ofilename'] += "Friend"
            self.cfg['ofilename'] += ".root"
        option += self.cfg['ofilename'] + ";"
#
        self.tree.Process(SingleBuToKstarMuMuSelector.cpp.modulePath + "/SingleBuToKstarMuMuSelector.C+", option)  # '+' is necessary for dynamic compile and load.

DATADIR="/eos/cms/store/user/pchen/BToKstarMuMu/dat/ntp/v3p2"
datasets = {}

# eventContent: "data"
baseCfg = copy(StdSelector.templateConfig())
datasets['Run2012'] = copy(baseCfg)
datasets['Run2012'].update({
    'datasetTag': 'Run2012',
    'ifile': [DATADIR + "/BuToKstarMuMu-data-2012*-v3p2-merged.root"],
})

# eventContent: "mc"
baseCfg.update({
    'isMC': True,
    'eventContent': "mc"
})
datasets['BuToKstarMuMu'] = copy(baseCfg)
datasets['BuToKstarMuMu'].update({
    'datasetTag': 'BToKstarMuMu',
    'ifile': [DATADIR + "/BuToKstarMuMu_8TeV_merged.root"],
})
for part in range(1, 4 + 1):
    datasets['BuToKstarMuMu-extended-part' + str(part)] = copy(baseCfg)
    datasets['BuToKstarMuMu-extended-part' + str(part)].update({
        'datasetTag': 'BToKstarMuMu-extended-part' + str(part),
        'ifile': [DATADIR + "/BuToKstarMuMu_8TeV_extended_part{0}.root".format(part)],
    })

# Format doesn't match and it's way slow to filter, please go for EvtGen
# datasets['BuToKstarMuMu-NoFilter'] = copy(baseCfg)
# datasets['BuToKstarMuMu-NoFilter'].update({
#     'datasetTag': 'BToKstarMuMu-NoFilter',
#     'ifile': [DATADIR + "/BuToKstarMuMu_NoFilter_8TeV_merged.root"],
#     'cutSet': "genonly",
# })

datasets['BuToKstarJPsi'] = copy(baseCfg)
datasets['BuToKstarJPsi'].update({
    'datasetTag': 'BToKstarJPsi',
    'ifile': [DATADIR + "/BuToKstarJPsi_8TeV_merged.root"],
})
datasets['BuToKstarJPsi-extended'] = copy(baseCfg)
datasets['BuToKstarJPsi-extended'].update({
    'datasetTag': 'BuToKstarJPsi-extended',
    'ifile': [DATADIR + "/BuToKstarJPsi_8TeV_extended_merged.root"],
})
datasets['BuToKstarPsi2S'] = copy(baseCfg)
datasets['BuToKstarPsi2S'].update({
    'datasetTag': 'BuToKstarPsi2S',
    'ifile': [DATADIR + "/BuToKstarPsi2S_8TeV_merged.root"],
})
datasets['BuToKstarPsi2S-extended'] = copy(baseCfg)
datasets['BuToKstarPsi2S-extended'].update({
    'datasetTag': 'BuToKstarPsi2S-extended',
    'ifile': [DATADIR + "/BuToKstarPsi2S_8TeV_extended_merged.root"],
})

if __name__ == '__main__':
    for dKey, dCfg in datasets.items():
        print(dKey, dCfg)
