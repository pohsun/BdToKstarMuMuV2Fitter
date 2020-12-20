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
float Define_LambdaMass(float Pippt, float Pipeta, float Pipphi, float Pimpt, float Pimeta, float Pimphi){
    TLorentzVector proton, pion;
    proton.SetPtEtaPhiM(Pippt, Pipeta, Pipphi, PROTON_MASS);
    pion.SetPtEtaPhiM(Pimpt, Pimeta, Pimphi, PION_MASS);
    if (proton.P() < pion.P()){
        proton.SetPtEtaPhiM(Pimpt, Pimeta, Pimphi, PROTON_MASS);
        pion.SetPtEtaPhiM(Pippt, Pipeta, Pipphi, PION_MASS);
    }
    return (proton+pion).Mag();
}
float Define_KshortMass(float Pippt, float Pipeta, float Pipphi, float Pimpt, float Pimeta, float Pimphi){
    TLorentzVector pip, pim;
    pim.SetPtEtaPhiM(Pimpt, Pimeta, Pimphi, PION_MASS);
    pip.SetPtEtaPhiM(Pippt, Pipeta, Pipphi, PION_MASS);
    return (pim+pip).Mag();
}
float Define_KstarMass(float Pippt, float Pipeta, float Pipphi, float Pimpt, float Pimeta, float Pimphi, float Trkpt, float Trketa, float Trkphi){
    TLorentzVector pip, pim, trk;
    pim.SetPtEtaPhiM(Pimpt, Pimeta, Pimphi, PION_MASS);
    pip.SetPtEtaPhiM(Pippt, Pipeta, Pipphi, PION_MASS);
    trk.SetPtEtaPhiM(Trkpt, Trketa, Trkphi, PION_MASS);
    return (pim+pip+trk).Mag();
}
float Define_LambdaBMass(float Pippt, float Pipeta, float Pipphi, float Pimpt, float Pimeta, float Pimphi, float Dimupt, float Dimueta, float Dimuphi, float Mumumass){
    TLorentzVector proton, pion;
    proton.SetPtEtaPhiM(Pippt, Pipeta, Pipphi, PROTON_MASS);
    pion.SetPtEtaPhiM(Pimpt, Pimeta, Pimphi, PION_MASS);
    if (proton.P() < pion.P()){
        proton.SetPtEtaPhiM(Pimpt, Pimeta, Pimphi, PROTON_MASS);
        pion.SetPtEtaPhiM(Pippt, Pipeta, Pipphi, PION_MASS);
    }
    TLorentzVector dimu;
    dimu.SetPtEtaPhiM(Dimupt, Dimueta, Dimuphi, Mumumass);
    return (proton+pion+dimu).Mag();
}
float Define_BdMass(float Pippt, float Pipeta, float Pipphi, float Pimpt, float Pimeta, float Pimphi, float Dimupt, float Dimueta, float Dimuphi, float Mumumass){
    TLorentzVector pip, pim, dimu;
    pip.SetPtEtaPhiM(Pippt, Pipeta, Pipphi, PION_MASS);
    pim.SetPtEtaPhiM(Pimpt, Pimeta, Pimphi, PION_MASS);
    dimu.SetPtEtaPhiM(Dimupt, Dimueta, Dimuphi, Mumumass);
    return (pip+pim+dimu).Mag();
}
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
"""
ROOT.gInterpreter.Declare(cimp_Define_LambdaMass)

if __name__ == '__main__':
    tree = ROOT.TChain("tree")
    for f in dataCollection.dataReaderCfg['ifile']:
        tree.Add(f)
    df = ROOT.RDataFrame(tree)\
        .Filter(anaSetup.q2bins['summary']['cutString'])\
        .Filter(anaSetup.bMassRegions['Fit']['cutString'])\
        .Filter(anaSetup.cut_passTrigger)\
        .Filter(anaSetup.cut_kshortWindow)\
        .Filter(anaSetup.cut_kstarMassWindow)\
        .Filter(anaSetup.cut_resonanceRej)\
        .Filter(anaSetup.cut_antiRadiation)\
        .Define("BdMass", "Define_BdMass(Pippt, Pipeta, Pipphi, Pimpt, Pimeta, Pimphi, Dimupt, Dimueta, Dimuphi, Mumumass)")\
        .Define("MuTrkMass", "Define_MuTrkMass(Bchg, Muppt, Mupeta, Mupphi, Mumpt, Mumeta, Mumphi, Trkpt, Trketa, Trkphi)")
    df_BdSR = df.Filter("BdMass > 5.20 && BdMass<5.36")
    df_vetoBdSR = df.Filter("BdMass < 5.20 || BdMass>5.36")
    hists = {}
    hists['h_BdMass_bin0'] = {
        'hist': df.Histo1D(("h_BdMass_bin0", "", 26, 4.76, 5.80), "BdMass"),
        'xTitle': varCollection.Bdmass.GetTitle()}
    hists['h_BdMass_bin1'] = {
        'hist': df.Filter(anaSetup.q2bins['belowJpsi']['cutString']).Histo1D(("h_BdMass_bin1", "", 26, 4.76, 5.80), "BdMass"),
        'xTitle': varCollection.Bdmass.GetTitle()}
    hists['h_BdMass_bin3'] = {
        'hist': df.Filter(anaSetup.q2bins['betweenPeaks']['cutString']).Histo1D(("h_BdMass_bin3", "", 26, 4.76, 5.80), "BdMass"),
        'xTitle': varCollection.Bdmass.GetTitle()}
    hists['h_BdMass_bin5'] = {
        'hist': df.Filter(anaSetup.q2bins['abovePsi2s']['cutString']).Histo1D(("h_BdMass_bin5", "", 26, 4.76, 5.80), "BdMass"),
        'xTitle': varCollection.Bdmass.GetTitle()}
    hists['h_Bmass_BdSR_bin0'] = {
        'hist': df_BdSR.Histo1D(("h_Bmass_BdSR_bin0", "", 4, 5.20, 5.36), "Bmass"),
        'xTitle': varCollection.Bmass.GetTitle()}
    hists['h_Bmass_BdSR_bin1'] = {
        'hist': df_BdSR.Filter(anaSetup.q2bins['belowJpsi']['cutString']).Histo1D(("h_Bmass_BdSR_bin1", "", 4, 5.20, 5.36), "Bmass"),
        'xTitle': varCollection.Bmass.GetTitle()}
    hists['h_Bmass_BdSR_bin3'] = {
        'hist': df_BdSR.Filter(anaSetup.q2bins['betweenPeaks']['cutString']).Histo1D(("h_Bmass_BdSR_bin3", "", 4, 5.20, 5.36), "Bmass"),
        'xTitle': varCollection.Bmass.GetTitle()}
    hists['h_Bmass_BdSR_bin5'] = {
        'hist': df_BdSR.Filter(anaSetup.q2bins['abovePsi2s']['cutString']).Histo1D(("h_Bmass_BdSR_bin5", "", 4, 5.20, 5.36), "Bmass"),
        'xTitle': varCollection.Bmass.GetTitle()}
    hists['h_CosThetaK_BdSR_bin1'] = {
        'hist': df_BdSR.Filter(anaSetup.q2bins['belowJpsi']['cutString']).Histo1D(("h_CosThetaK_BdSR_bin1", "", 16, -1, 1.), "CosThetaK"),
        'yTitle': "Events",
        'xTitle': varCollection.CosThetaK.GetTitle()}
    hists['h_CosThetaK_BdMass510-520_bin1'] = {
        'hist': df.Filter(anaSetup.q2bins['belowJpsi']['cutString']).Filter("BdMass>5.10 && BdMass<5.20").Histo1D(("h_CosThetaK_BdMass512-522_bin1", "", 16, -1, 1.), "CosThetaK"),
        'yTitle': "Events",
        'xTitle': varCollection.CosThetaK.GetTitle()}
    hists['h_CosThetaK_BdMass520-536_bin1'] = {
        'hist': df.Filter(anaSetup.q2bins['belowJpsi']['cutString']).Filter("BdMass>5.20 && BdMass<5.36").Histo1D(("h_CosThetaK_BdMass522-534_bin1", "", 16, -1, 1.), "CosThetaK"),
        'yTitle': "Events",
        'xTitle': varCollection.CosThetaK.GetTitle()}
    hists['h_CosThetaK_BdMass536-560_bin1'] = {
        'hist': df.Filter(anaSetup.q2bins['belowJpsi']['cutString']).Filter("BdMass>5.36 && BdMass<5.60").Histo1D(("h_CosThetaK_BdMass534-560_bin1", "", 16, -1, 1.), "CosThetaK"),
        'yTitle': "Events",
        'xTitle': varCollection.CosThetaK.GetTitle()}
    hists['h_CosThetaK_USB_bin1'] = {
        'hist': df.Filter(anaSetup.q2bins['belowJpsi']['cutString']).Filter(anaSetup.bMassRegions['USB']['cutString']).Histo1D(("h_CosThetaK_USB_bin1", "", 16, -1, 1.), "CosThetaK"),
        'yTitle': "Events",
        'xTitle': varCollection.CosThetaK.GetTitle()}
    hists['h_CosThetaK_LSB_bin1'] = {
        'hist': df.Filter(anaSetup.q2bins['belowJpsi']['cutString']).Filter(anaSetup.bMassRegions['LSB']['cutString']).Histo1D(("h_CosThetaK_LSB_bin1", "", 16, -1, 1.), "CosThetaK"),
        'yTitle': "Events",
        'xTitle': varCollection.CosThetaK.GetTitle()}

    canvas = Plotter.canvas
    canvas.cd()
    line = ROOT.TLine()
    line.SetLineColor(2)
    line.SetLineWidth(2)
    line.SetLineStyle(10)
    for hName, hData in hists.items():
        hData['hist'].SetMinimum(0)
        hData['hist'].SetMaximum(hData['hist'].GetMaximum()*1.8)
        hData['hist'].SetNdivisions(510, "X")
        hData['hist'].GetXaxis().SetTitle(hData.get('xTitle', ""))
        hData['hist'].GetYaxis().SetTitle(hData.get('yTitle', "Events / 40 MeV"))
        hData['hist'].Draw("E")
        if hName == "h_BdMass_bin0":
            f = ROOT.TF1("f", "gaus(0)+expo(3)", 4.76, 5.80)
            f.SetParameter(0, 5)
            f.SetParLimits(0, 0., 20)
            f.SetParameter(1, 5.28)
            f.SetParLimits(1, 5.25, 5.31)
            f.SetParameter(2, 0.05)
            f.SetParLimits(2, 0.01, 0.1)
            hData['hist'].Fit("f", "LE0") # "0" option turns off plotting
	if re.match('h_BdMass_bin[0135]', hName):
	    line.DrawLine(5.20, hData['hist'].GetMinimum(), 5.20, hData['hist'].GetMaximum())
	    line.DrawLine(5.36, hData['hist'].GetMinimum(), 5.36, hData['hist'].GetMaximum())
        Plotter.latexDataMarks()
	canvas.Update()
        canvas.Print(hName+".pdf")
