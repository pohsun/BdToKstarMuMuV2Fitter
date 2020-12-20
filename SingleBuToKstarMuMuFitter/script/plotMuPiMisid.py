#!/usr/bin/env python

import re
import ROOT

import SingleBuToKstarMuMuFitter.anaSetup as anaSetup
import SingleBuToKstarMuMuFitter.dataCollection as dataCollection
import SingleBuToKstarMuMuFitter.varCollection as varCollection
from SingleBuToKstarMuMuFitter.plotCollection import Plotter as Plotter

cimp_Define_LambdaMass = """
const float MUON_MASS = 0.10566;
const float PION_MASS = 0.13957018;
const float PROTON_MASS = 0.938272;
float Define_MuTrkMass(int Bchg, float Muppt, float Mupeta, float Mupphi, float Mumpt, float Mumeta, float Mumphi, float Trkpt, float Trketa, float Trkphi){
    TLorentzVector mu, trk;
    trk.SetPtEtaPhiM(Trkpt, Trketa, Trkphi, MUON_MASS);
    if (Bchg > 0){
        mu.SetPtEtaPhiM(Mumpt, Mumeta, Mumphi, MUON_MASS);
    }else{
        mu.SetPtEtaPhiM(Muppt, Mupeta, Mupphi, MUON_MASS);
    }
    return (mu+trk).Mag();
}
float Define_BdMass(float Pippt, float Pipeta, float Pipphi, float Pimpt, float Pimeta, float Pimphi, float Dimupt, float Dimueta, float Dimuphi, float Mumumass){
    TLorentzVector pip, pim, dimu;
    pip.SetPtEtaPhiM(Pippt, Pipeta, Pipphi, PION_MASS);
    pim.SetPtEtaPhiM(Pimpt, Pimeta, Pimphi, PION_MASS);
    dimu.SetPtEtaPhiM(Dimupt, Dimueta, Dimuphi, Mumumass);
    return (pip+pim+dimu).Mag();
}
"""
ROOT.gInterpreter.Declare(cimp_Define_LambdaMass)

if __name__ == '__main__':
    tree_data = ROOT.TChain("tree")
    for f in dataCollection.dataReaderCfg['ifile']:
        tree_data.Add(f)
    tree_jpsi = ROOT.TChain("tree")
    for f in dataCollection.bkgJpsiMCReaderCfg['ifile']:
        tree_jpsi.Add(f)
    
    df_data = ROOT.RDataFrame(tree_data)\
        .Filter(anaSetup.q2bins['summary']['cutString'])\
        .Filter(anaSetup.bMassRegions['Fit']['cutString'])\
        .Filter(anaSetup.cut_passTrigger)\
        .Filter(anaSetup.cut_kshortWindow)\
        .Filter(anaSetup.cut_kstarMassWindow)\
        .Filter(anaSetup.cut_resonanceRej)\
        .Filter(anaSetup.cut_antiRadiation)\
        .Define("BdMass", "Define_BdMass(Pippt, Pipeta, Pipphi, Pimpt, Pimeta, Pimphi, Dimupt, Dimueta, Dimuphi, Mumumass)")\
        .Define("MuTrkMass", "Define_MuTrkMass(Bchg, Muppt, Mupeta, Mupphi, Mumpt, Mumeta, Mumphi, Trkpt, Trketa, Trkphi)")
    df_jpsi = ROOT.RDataFrame(tree_jpsi)\
        .Filter(anaSetup.q2bins['summary']['cutString'])\
        .Filter(anaSetup.bMassRegions['Fit']['cutString'])\
        .Filter(anaSetup.cut_passTrigger)\
        .Filter(anaSetup.cut_kshortWindow)\
        .Filter(anaSetup.cut_kstarMassWindow)\
        .Filter(anaSetup.cut_resonanceRej)\
        .Filter(anaSetup.cut_antiRadiation)\
        .Define("BdMass", "Define_BdMass(Pippt, Pipeta, Pipphi, Pimpt, Pimeta, Pimphi, Dimupt, Dimueta, Dimuphi, Mumumass)")\
        .Define("MuTrkMass", "Define_MuTrkMass(Bchg, Muppt, Mupeta, Mupphi, Mumpt, Mumeta, Mumphi, Trkpt, Trketa, Trkphi)")
    filterStr_BdSR = "BdMass > 5.20 && BdMass<5.36"
    filterStr_vetoSR = "BdMass < 5.20 || BdMass>5.36"

    hists = {}
    hists['h_MuTrkMass_jpsi_bin0'] = {
        'hist': df_jpsi.Histo1D(("h_MuTrkMass_jpsi_bin0", "", 85, 1., 4.4), "MuTrkMass"),
        'latexDataMarks': 'sim',
        'yTitle': "Events/ 40 MeV",
        'xTitle': varCollection.Mumumass.GetTitle(),
        'scale': dataCollection.dataReaderCfg['lumi']/dataCollection.bkgJpsiMCReaderCfg['lumi']}
    hists['h_BdMass_jpsi_bin0'] = {
        'hist': df_jpsi.Histo1D(("h_BdMass_jpsi_bin0", "", 26, 4.76, 5.80), "BdMass"),
        'latexDataMarks': 'sim',
        'xTitle': varCollection.Bdmass.GetTitle(),
        'scale': dataCollection.dataReaderCfg['lumi']/dataCollection.bkgJpsiMCReaderCfg['lumi']}
    hists['h_Bmass_jpsi_BdSR_bin0'] = {
        'hist': df_jpsi.Filter(filterStr_BdSR).Histo1D(("h_Bmass_jpsi_BdSR_bin0", "", 26, 4.76, 5.80), "Bmass"),
        'latexDataMarks': 'sim',
        'xTitle': varCollection.Bmass.GetTitle(),
        'scale': dataCollection.dataReaderCfg['lumi']/dataCollection.bkgJpsiMCReaderCfg['lumi']}
    hists['h_CosThetaK_jpsi_BdSR_bin1'] = {
        'hist': df_jpsi.Filter(filterStr_BdSR).Filter(anaSetup.q2bins['belowJpsi']['cutString']).Histo1D(("h_CosThetaK_jpsi_BdSR_bin1", "", 16, -1, 1.), "CosThetaK"),
        'latexDataMarks': 'sim',
        'xTitle': varCollection.CosThetaK.GetTitle(),
        'scale': dataCollection.dataReaderCfg['lumi']/dataCollection.bkgJpsiMCReaderCfg['lumi']}
    hists['h_MuTrkMass_data_bin0'] = {
        'hist': df_data.Histo1D(("h_MuTrkMass_data_bin0", "", 85, 1.0, 4.4), "MuTrkMass"),
        'latexDataMarks': '',
        'yTitle': "Events/ 40 MeV",
        'xTitle': varCollection.Mumumass.GetTitle()}
    hists['h_BdMass_data_bin0'] = {
        'hist': df_data.Histo1D(("h_BdMass_data_bin0", "", 26, 4.76, 5.80), "BdMass"),
        'latexDataMarks': '',
        'xTitle': varCollection.Bdmass.GetTitle(),}
    hists['h_Bmass_data_BdSR_bin0'] = {
        'hist': df_data.Filter(filterStr_BdSR).Histo1D(("h_Bmass_data_BdSR_bin0", "", 26, 4.76, 5.80), "Bmass"),
        'latexDataMarks': '',
        'xTitle': varCollection.Bmass.GetTitle(),}
    hists['h_CosThetaK_data_BdSR_bin1'] = {
        'hist': df_data.Filter(filterStr_BdSR).Filter(anaSetup.q2bins['belowJpsi']['cutString']).Histo1D(("h_CosThetaK_data_BdSR_bin1", "", 16, -1, 1.), "CosThetaK"),
        'latexDataMarks': '',
        'xTitle': varCollection.CosThetaK.GetTitle()}

    canvas = Plotter.canvas
    canvas.cd()
    line = ROOT.TLine()
    line.SetLineColor(2)
    line.SetLineWidth(2)
    line.SetLineStyle(10)
    for hName, hData in hists.items():
        hData['hist'].SetNdivisions(510, "X")
        hData['hist'].GetXaxis().SetTitle(hData.get('xTitle', ""))
        hData['hist'].GetYaxis().SetTitle(hData.get('yTitle', "Events"))
        hData['hist'].Scale(hData.get('scale', 1))
        hData['hist'].Draw("E")
	if hName in ['h_MuTrkMass_data_bin0', 'h_MuTrkMass_jpsi_bin0']:
	    line.DrawLine(2.95, 0, 2.95, hData['hist'].GetMaximum()*1.8)
	    line.DrawLine(3.18, 0, 3.18, hData['hist'].GetMaximum()*1.8)
        if re.match("h_.*_jpsi_.*", hName):
            Plotter.latexLumi()
        Plotter.latexDataMarks(hData.get('latexDataMarks', ''))
        hData['hist'].SetMinimum(0)
        hData['hist'].SetMaximum(hData['hist'].GetMaximum()*1.8)
        canvas.Update()
        canvas.Print(hName+".pdf")

        print(hName, hData['hist'].GetSumOfWeights())
