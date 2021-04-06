/***************************************************************************************
                                    * Mission Analyzer
                                * Project : Rails Splicing
                            * Author : Loïc SANDRAS - INSA Trainee
                                    * Date : 08/2020
 ***************************************************************************************/

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Threading;
using System.Windows.Forms;
using System.Xml.Serialization;
using System.IO;
using System.Collections;
using System.Xml;
using System.Security.Cryptography.X509Certificates;
using System.Drawing.Text;
using System.Diagnostics;
using System.Runtime.CompilerServices;
using INFITF;
using MECMOD;
using KnowledgewareTypeLib;
using System.Runtime.InteropServices;

namespace DataAnalyser
{
    public partial class Form1 : Form
    {
        /****************************************
               Déclaration des variables
         ***************************************/
        private BackgroundWorker bgw_conversion;
        private XmlWriter xmlWriter;

        //Déclaration des listes de trajectoires 
        private List<Joint> WebAv;
        private List<Joint> WebAr;
        private List<Joint> FlangeAvExte;
        private List<Joint> FlangeAvInte;
        private List<Joint> FlangeArExte;
        private List<Joint> FlangeArInte;

        public static Double Flange_Offset1 = 14; //Ask
        public static Double Flange_Offset2 = 11; //Ask
        public static Double YRail1;
        String[] FastenerName_CATIA = { "asna", "en6115" }; //Nom des Fastener sur le CADFILE -> On peut demander au préparateur de les donner

        /****************************************************************
             Création d'une classe recensant toutes les données CATIA
        ****************************************************************/
        public class CatiaData
        {
            public CatiaData(string Name, double[] param)
            {
                this.Name = Name;
                this.XValue = param[0];
                this.YValue = param[1];
                this.ZValue = param[2];
                this.XDir = param[3];
                this.YDir = param[4];
                this.ZDir = param[5];
                this.Diameter = param[7];
                this.Length = param[8];
                this.Depth = param[9];
            }

            public string Name { get; set; }
            public double XValue { get; set; }
            public double YValue { get; set; }
            public double ZValue { get; set; }
            public double XDir { get; set; }
            public double YDir { get; set; }
            public double ZDir { get; set; }
            public double Diameter { get; set; }
            public double Length { get; set; }
            public double Depth { get; set; }
        }

        /**************************************************************************
             Création d'une classe Joint pour la définition des trajectoires
        **************************************************************************/
        public class Joint
        {
            public Double J1 { get; set; }
            public Double J2 { get; set; }
            public Double J3 { get; set; }
            public Double J4 { get; set; }
            public Double J5 { get; set; }
            public Double J6 { get; set; }
        } 

        //Mini IHM -> A développer
        public Form1()
        {
            InitializeComponent();

            this.bgw_conversion = new BackgroundWorker();
            this.bgw_conversion.DoWork += new DoWorkEventHandler(bgw_conversion_DoWork);
        }

        private void bgw_conversion_DoWork(object sender, DoWorkEventArgs e)
        {
            /****************************************************
                     Création des données Points à percer
            ****************************************************/
            List<Point> DrillingPoints;
            DrillingPoints = GetCatiaData();

            /****************************************************
                     Création du BuildProcess
                     Création de fichier Xml
            ****************************************************/
            BuildProcess_Creation(DrillingPoints);

            //Ouverture du Fichier Xml pour vérifications
            System.Diagnostics.Process.Start(@"C:\Users\Virtual\Source\Repos\RailsSplicing\BuildProcess.xml");
        }

        //Lancement du Process de Conversion
        private void button1_Click(object sender, EventArgs e)
        {
            bgw_conversion.RunWorkerAsync(2000);
        }

        /****************************************************
             Récupération des Données CATIA (Fasteners)
        ****************************************************/
        private List<Point> GetCatiaData()
        {
            List<Point> liste = new List<Point>();
            INFITF.Application catia;
            try
            {
                catia = (INFITF.Application)Marshal.GetActiveObject("CATIA.Appication");
            }
            catch (Exception)
            {
                catia = (INFITF.Application)Activator.CreateInstance(Type.GetTypeFromProgID("CATIA.Application"));
            }
            catia.Visible = true;

            PartDocument prtDoc = (PartDocument)catia.Documents.Open(@"C:\Users\Virtual\Source\Repos\DataAnalyser\RailsSplicing.CATPart");
            
            INFITF.Selection oSelection1;
            INFITF.Selection oSelection2;
            oSelection1 = catia.ActiveDocument.Selection;
            oSelection2 = catia.ActiveDocument.Selection;

            //Récupération des Données CATIA grâce à la classe CatiaData
            List<CatiaData> listeData = new List<CatiaData>(); //Liste contenant l'ensemble des données
            //autant de récupération de data que de nom de Fastener 
            foreach(String s in FastenerName_CATIA)
            {
                List<CatiaData> liste1 = CatiaSelection(oSelection1, s);
                foreach (CatiaData data in liste1)
                    listeData.Add(data);
            }

            List<Double> Rails = DefineRails(listeData); //Trouv les coord Y des 6 Rails
            YRail1 = Rails[0]; //Coordonnée Y du 1er Rail -> E1 = 0
            
            //Créer un Point à partir de la coordonnée CATIA
            foreach (CatiaData data in listeData)
                liste.Add(new Point(data, Rails));
            
            prtDoc.Close();
            catia.Application.Quit();
            return liste;
        }

        /*******************************************************************
                     Sélection des Données CATIA (Fasteners)
             Ecriture des informations Fasteners dans des fichiers .txt
                           Conversion Fastener -> Point
        *******************************************************************/
        private List<CatiaData> CatiaSelection(INFITF.Selection oSelection, String s)
        {
            int iCount, sEnd, sLen;
            string sSearch;
            string sValue;

            HybridShapeInstance oSelectedItem;
            Parameter oParam;

            sSearch = "Name="+s+"*,all";
            oSelection.Search(sSearch);
            iCount = oSelection.Count;

            List<CatiaData> pt = new List<CatiaData>();
            double[] ptValues = new double[10];

            for (int i = 1; i <= iCount; i++)
            {
                oSelectedItem = (HybridShapeInstance)oSelection.Item(i).Value;
                for (int j = 1; j <= 10; j++)
                {
                    oParam = (Parameter)oSelectedItem.GetParameterFromPosition(j);
                    sValue = oParam.ValueAsString();
                    switch (j)
                    {
                        case 7:
                            ptValues[j - 1] = 0;
                            break;
                        case 4:
                        case 5:
                        case 6:
                            ptValues[j - 1] = Double.Parse(sValue);
                            break;
                        default:
                            sEnd = sValue.IndexOf("mm");
                            sLen = sValue.Length;
                            ptValues[j - 1] = Double.Parse(sValue.Substring(0, sEnd));
                            break;

                    }
                }
                pt.Add(new CatiaData(oSelectedItem.get_Name(), ptValues));
            }

            //Ecriture Fichier .txt contenant toutes les data Fasteners 
            string sMessage;
            using (System.IO.StreamWriter file = new System.IO.StreamWriter(@"c:\Users\Virtual\Source\Repos\DataAnalyser\List of points "+s+".txt"))
            {
                for (int i = 0; i < iCount; i++)
                {
                    sMessage = "Name: " + pt[i].Name;
                    file.WriteLine(sMessage);
                    sMessage = "Xe: " + pt[i].XValue;
                    file.WriteLine(sMessage);
                    sMessage = "Ye: " + pt[i].YValue;
                    file.WriteLine(sMessage);
                    sMessage = "Ze: " + pt[i].ZValue;
                    file.WriteLine(sMessage);
                    sMessage = "XDir: " + pt[i].XDir;
                    file.WriteLine(sMessage);
                    sMessage = "YDir: " + pt[i].YDir;
                    file.WriteLine(sMessage);
                    sMessage = "ZDir: " + pt[i].ZDir;
                    file.WriteLine(sMessage);
                    sMessage = "Diameter: " + pt[i].Diameter;
                    file.WriteLine(sMessage);
                    sMessage = "Depth: " + pt[i].Depth;
                    file.WriteLine(sMessage);
                }
            }

            oSelection.Clear();
            return pt;
        }

        /*********************************************************
            Création de la structure du Build Process (en dur)
               Création des Phases à partir des data Point
               Ajouts des Phases dans les bonnes stations
        *********************************************************/
        private void BuildProcess_Creation(List<Point> DrillingPoints)
        {
            //Création des 4 steps -> On pourrait demander à l'opérateur les bons diamètres -> autant de step que de combinaisons C/Diam
            List<Step> steps = new List<Step>();
            steps.Add(new Step("Web", 4.8));
            steps.Add(new Step("Web", 4.0));
            steps.Add(new Step("Flange", 4.8));
            steps.Add(new Step("Flange", 4.2));

            //Création des Stations -> On pourrait demander à l'opérateur d'indiquer l'ensemble des stations (rail, côté, position)
            //Stations pour le Step 1
            steps[0].station.Add(new Station(1, "Front"));
            steps[0].station.Add(new Station(1, "Back"));
            steps[0].station.Add(new Station(2, "Front"));
            steps[0].station.Add(new Station(2, "Back"));
            steps[0].station.Add(new Station(5, "Front"));
            steps[0].station.Add(new Station(5, "Back"));
            steps[0].station.Add(new Station(6, "Front"));
            steps[0].station.Add(new Station(6, "Back"));

            //Stations pour le step 2
            steps[1].station.Add(new Station(3, "Front"));
            steps[1].station.Add(new Station(3, "Back"));
            steps[1].station.Add(new Station(4, "Front"));
            steps[1].station.Add(new Station(4, "Back"));

            //Stations pour le step 3
            steps[2].station.Add(new Station(1, "Front", "R"));
            steps[2].station.Add(new Station(1, "Back", "R"));
            steps[2].station.Add(new Station(2, "Front", "L"));
            steps[2].station.Add(new Station(2, "Back", "L"));
            steps[2].station.Add(new Station(2, "Front", "R"));
            steps[2].station.Add(new Station(2, "Back", "R"));
            steps[2].station.Add(new Station(5, "Front", "L"));
            steps[2].station.Add(new Station(5, "Back", "L"));
            steps[2].station.Add(new Station(5, "Front", "R"));
            steps[2].station.Add(new Station(5, "Back", "R"));
            steps[2].station.Add(new Station(6, "Front", "L"));
            steps[2].station.Add(new Station(6, "Back", "L"));

            //Station pour le step 4
            steps[3].station.Add(new Station(3, "Front", "L"));
            steps[3].station.Add(new Station(3, "Back", "L"));
            steps[3].station.Add(new Station(3, "Front", "R"));
            steps[3].station.Add(new Station(3, "Back", "R"));
            steps[3].station.Add(new Station(4, "Front", "L"));
            steps[3].station.Add(new Station(4, "Back", "L"));
            steps[3].station.Add(new Station(4, "Front", "R"));
            steps[3].station.Add(new Station(4, "Back", "R"));

            /****************************************************
               Création des phases à partir des points à percer
            ****************************************************/

            //Ajout des phases dans la bonne station selon les règles 
            foreach (Point pnt in DrillingPoints)
            {
                if (pnt.C == "Web" && pnt.Diameter == 4.8)
                {
                    if (pnt.Rail == 1)
                    {
                        if (pnt.Position == "Front")
                        {
                            steps[0].station[0].phases.Add(new Phase(pnt));
                        }
                        else if (pnt.Position == "Back")
                        {
                            steps[0].station[1].phases.Add(new Phase(pnt));
                        }
                    }

                    else if (pnt.Rail == 2)
                    {
                        if (pnt.Position == "Front")
                        {
                            steps[0].station[2].phases.Add(new Phase(pnt));
                        }
                        else if (pnt.Position == "Back")
                        {
                            steps[0].station[3].phases.Add(new Phase(pnt));
                        }
                    }

                    else if (pnt.Rail == 5)
                    {
                        if (pnt.Position == "Front")
                        {
                            steps[0].station[4].phases.Add(new Phase(pnt));
                        }
                        else if (pnt.Position == "Back")
                        {
                            steps[0].station[5].phases.Add(new Phase(pnt));
                        }
                    }

                    else if (pnt.Rail == 6)
                    {
                        if (pnt.Position == "Front")
                        {
                            steps[0].station[6].phases.Add(new Phase(pnt));
                        }
                        else if (pnt.Position == "Back")
                        {
                            steps[0].station[7].phases.Add(new Phase(pnt));
                        }
                    }
                }

                if (pnt.C == "Web" && pnt.Diameter == 4)
                {
                    if (pnt.Rail == 3)
                    {
                        if (pnt.Position == "Front")
                        {
                            steps[1].station[0].phases.Add(new Phase(pnt));
                        }
                        else if (pnt.Position == "Back")
                        {
                            steps[1].station[1].phases.Add(new Phase(pnt));
                        }
                    }

                    else if (pnt.Rail == 4)
                    {
                        if (pnt.Position == "Front")
                        {
                            steps[1].station[2].phases.Add(new Phase(pnt));
                        }
                        else if (pnt.Position == "Back")
                        {
                            steps[1].station[3].phases.Add(new Phase(pnt));
                        }
                    }
                }

                if (pnt.C == "Flange" && pnt.Diameter == 4.8)
                {
                    if (pnt.X > 45 || pnt.X < 0) //Points accessibles
                    {
                        if (pnt.Rail == 1)
                        {
                            if (pnt.Side == "R")
                            {
                                if (pnt.Position == "Front")
                                    steps[2].station[0].phases.Add(new Phase(pnt));
                                else if (pnt.Position == "Back")
                                    steps[2].station[1].phases.Add(new Phase(pnt));
                            }
                        }

                        if (pnt.Rail == 2)
                        {
                            if (pnt.Side == "L")
                            {
                                if (pnt.Position == "Front")
                                    steps[2].station[2].phases.Add(new Phase(pnt));
                                else if (pnt.Position == "Back")
                                    steps[2].station[3].phases.Add(new Phase(pnt));
                            }
                            else if (pnt.Side == "R")
                            {
                                if (pnt.Position == "Front")
                                    steps[2].station[4].phases.Add(new Phase(pnt));
                                else if (pnt.Position == "Back")
                                    steps[2].station[5].phases.Add(new Phase(pnt));
                            }
                        }

                        else if (pnt.Rail == 5)
                        {
                            if (pnt.Side == "L")
                            {
                                if (pnt.Position == "Front")
                                    steps[2].station[6].phases.Add(new Phase(pnt));
                                else if (pnt.Position == "Back")
                                    steps[2].station[7].phases.Add(new Phase(pnt));
                            }
                            else if (pnt.Side == "R")
                            {
                                if (pnt.Position == "Front")
                                    steps[2].station[8].phases.Add(new Phase(pnt));
                                else if (pnt.Position == "Back")
                                    steps[2].station[9].phases.Add(new Phase(pnt));
                            }
                        }

                        else if (pnt.Rail == 6)
                        {
                            if (pnt.Side == "L")
                            {
                                if (pnt.Position == "Front")
                                    steps[2].station[10].phases.Add(new Phase(pnt));
                                else if (pnt.Position == "Back")
                                    steps[2].station[11].phases.Add(new Phase(pnt));
                            }
                        }
                    }
                }

                if (pnt.C == "Flange" && pnt.Diameter == 4.2)
                {
                    if (pnt.X > 45 || pnt.X < 0)
                    {
                        if (pnt.Rail == 3)
                        {
                            if (pnt.Side == "L")
                            {
                                if (pnt.Position == "Front")
                                    steps[3].station[0].phases.Add(new Phase(pnt));
                                else if (pnt.Position == "Back")
                                    steps[3].station[1].phases.Add(new Phase(pnt));
                            }
                            else if (pnt.Side == "R")
                            {
                                if (pnt.Position == "Front")
                                    steps[3].station[2].phases.Add(new Phase(pnt));
                                else if (pnt.Position == "Back")
                                    steps[3].station[3].phases.Add(new Phase(pnt));
                            }
                        }

                        if (pnt.Rail == 4)
                        {
                            if (pnt.Side == "L")
                            {
                                if (pnt.Position == "Front")
                                    steps[3].station[4].phases.Add(new Phase(pnt));
                                else if (pnt.Position == "Back")
                                    steps[3].station[5].phases.Add(new Phase(pnt));
                            }
                            else if (pnt.Side == "R")
                            {
                                if (pnt.Position == "Front")
                                    steps[3].station[6].phases.Add(new Phase(pnt));
                                else if (pnt.Position == "Back")
                                    steps[3].station[7].phases.Add(new Phase(pnt));
                            }
                        }
                    }
                }
            }

            //Tri des stations pour percer du plus loin au plus prêt du rail transversal
            foreach (Step step in steps)
            {
                foreach (Station station in step.station)
                {
                    List<Phase> phase = station.phases;
                    triStation(phase, step.C);
                }
            }
            
            writeXml(steps); //Ecriture du Fichier Xml : AR File
        }

        /******************************************************
                           Tri des stations
        ******************************************************/
        private void triStation(List<Phase> phase, String C)
        {
            int ndebut = 0;
            int nfin = phase.Count - 1;
            while (ndebut < nfin)
            {
                int debut = ndebut;
                int fin = nfin;
                ndebut = phase.Count;
                for (int i = debut; i < fin; i++)
                {
                    if (Math.Abs(phase[i].X) < Math.Abs(phase[i + 1].X))
                    {
                        Phase trans = phase[i];
                        phase[i] = phase[i + 1];
                        phase[i + 1] = trans;
                        if (i < ndebut)
                        {
                            ndebut = i - 1;
                            if (ndebut < 0)
                            {
                                ndebut = 0;
                            }
                        }
                        else if (i > nfin)
                        {
                            nfin = i + 1;
                        }
                    }
                }
            }
        }

        /******************************************************
                         Ecriture du Fichier Xml
        ******************************************************/
        private void writeXml(List<Step> steps)
        {

            /*************************************************************************
                                   Ecriture des Trajectoire 
                       Obtentions des Datas : Arbitrairement via RoboGuide
            *************************************************************************/

            WebAv = new List<Joint>();
            WebAv.Add(new Joint { J1 = 0, J2 = 25, J3 = -40, J4 = 0, J5 = 113, J6 = 0 }); //Home
            WebAv.Add(new Joint { J1 = 20, J2 = 35, J3 = -30, J4 = -40, J5 = 105, J6 = 90 }); //Point 1
            WebAv.Add(new Joint { J1 = 40, J2 = 45, J3 = -15, J4 = -60, J5 = 105, J6 = 90 }); //Point 2
            WebAv.Add(new Joint { J1 = 60, J2 = 60, J3 = -10, J4 = -80, J5 = 60, J6 = 110 }); //Point 3
            WebAv.Add(new Joint { J1 = 60, J2 = 53, J3 = -2, J4 = -92, J5 = 47, J6 = 137 }); //Point 4
            WebAv.Add(new Joint { J1 = 60.1, J2 = 53.2, J3 = -2, J4 = -120, J5 = 25, J6 = 150 }); //Point 5
            WebAv.Add(new Joint { J1 = 60.1, J2 = 53.2, J3 = -5.6, J4 = -169, J5 = 24.9, J6 = 222 }); //Point 6
            WebAv.Add(new Joint { J1 = 57.9, J2 = 57.9, J3 = -6.9, J4 = -173.1, J5 = 23.3, J6 = 226.9 }); //Point 7

            WebAr = new List<Joint>();
            WebAr.Add(new Joint { J1 = 0, J2 = 25, J3 = -40, J4 = 0, J5 = 113, J6 = 0 }); //Home
            WebAr.Add(new Joint { J1 = 20, J2 = 35, J3 = -30, J4 = -40, J5 = 105, J6 = 90 }); //Point 1
            WebAr.Add(new Joint { J1 = 40, J2 = 45, J3 = -15, J4 = -60, J5 = 105, J6 = 90 }); //Point 2
            WebAr.Add(new Joint { J1 = 60, J2 = 60, J3 = -10, J4 = -80, J5 = 60, J6 = 110 }); //Point 3
            WebAr.Add(new Joint { J1 = 67.5, J2 = 58, J3 = -8.5, J4 = -91.8, J5 = 47.5, J6 = 137 }); //Point 4
            WebAr.Add(new Joint { J1 = 69.9, J2 = 64.4, J3 = -10.6, J4 = -105.2, J5 = 23.9, J6 = 152.3 }); //Point 5
            WebAr.Add(new Joint { J1 = 74.9, J2 = 69, J3 = -15, J4 = -132.4, J5 = 23.9, J6 = 179.3 }); //Point 6
            WebAr.Add(new Joint { J1 = 72.2, J2 = 74.8, J3 = -15.5, J4 = -135.2, J5 = 21.7, J6 = 183.1 }); //Point 7

            FlangeAvExte = new List<Joint>();
            FlangeAvExte.Add(new Joint { J1 = 0, J2 = 25, J3 = -40, J4 = 0, J5 = 113, J6 = 0 }); //Home
            FlangeAvExte.Add(new Joint { J1 = 32.2, J2 = 37.4, J3 = -45.2, J4 = -22.2, J5 = 94.6, J6 = 112.1 }); //Point 1
            FlangeAvExte.Add(new Joint { J1 = 45.2, J2 = 52.8, J3 = -26.4, J4 = -30.4, J5 = 80.4, J6 = 129.9 }); //Point 2
            FlangeAvExte.Add(new Joint { J1 = 52.8, J2 = 43.2, J3 = -28.7, J4 = -35.8, J5 = 45.9, J6 = 137.7 }); //Point 3
            FlangeAvExte.Add(new Joint { J1 = 49.5, J2 = 43.3, J3 = -2, J4 = -150, J5 = 56.5, J6 = 210.7 }); //Point 4
            FlangeAvExte.Add(new Joint { J1 = 41.9, J2 = 49.2, J3 = -16.4, J4 = -145.5, J5 = 36.4, J6 = 211 }); //Point 5
            FlangeAvExte.Add(new Joint { J1 = 38.7, J2 = 43.3, J3 = -20.7, J4 = -144.6, J5 = 31.1, J6 = 211 }); //Point 6

            FlangeArExte = new List<Joint>();
            FlangeArExte.Add(new Joint { J1 = 0, J2 = 25, J3 = -40, J4 = 0, J5 = 113, J6 = 0 }); //Home
            FlangeArExte.Add(new Joint { J1 = 40.3, J2 = 39.5, J3 = -48.6, J4 = -27.7, J5 = 100, J6 = 115.8 }); //Point 1
            FlangeArExte.Add(new Joint { J1 = 72.3, J2 = 62.8, J3 = -62.2, J4 = -50, J5 = 104, J6 = 120 }); //Point 2
            FlangeArExte.Add(new Joint { J1 = 70.3, J2 = 71.3, J3 = -63, J4 = -51.3, J5 = 98.9, J6 = 120 }); //Point 3
            FlangeArExte.Add(new Joint { J1 = 70.2, J2 = 57.2, J3 = -54.7, J4 = -73.4, J5 = 60.7, J6 = 128.3 }); //Point 4
            FlangeArExte.Add(new Joint { J1 = 62.4, J2 = 57.8, J3 = -46.9, J4 = -103.3, J5 = 35.5, J6 = 147.9 }); //Point 5
            FlangeArExte.Add(new Joint { J1 = 59.5, J2 = 52.6, J3 = -50.3, J4 = -96.4, J5 = 31, J6 = 142.2 }); //Point 6

            FlangeAvInte = new List<Joint>();
            FlangeAvInte.Add(new Joint { J1 = 0, J2 = 25, J3 = -40, J4 = 0, J5 = 113, J6 = 0 }); //Home
            FlangeAvInte.Add(new Joint { J1 = 24, J2 = 32.8, J3 = -57.5, J4 = -17.3, J5 = 104.5, J6 = -76.9 }); //Point 1
            FlangeAvInte.Add(new Joint { J1 = 27.9, J2 = 37.4, J3 = -56.7, J4 = -30.3, J5 = 86.6, J6 = -73 }); //Point 2
            FlangeAvInte.Add(new Joint { J1 = 32.4, J2 = 32.8, J3 = -48.9, J4 = -50.5, J5 = 61, J6 = -59.6 }); //Point 3
            FlangeAvInte.Add(new Joint { J1 = 34.5, J2 = 32.7, J3 = -41.5, J4 = -68.9, J5 = 47, J6 = -41 }); //Point 4
            FlangeAvInte.Add(new Joint { J1 = 36.3, J2 = 35.9, J3 = -27.6, J4 = -129.9, J5 = 46, J6 = 20 }); //Point 5
            FlangeAvInte.Add(new Joint { J1 = 38.5, J2 = 43, J3 = -20.9, J4 = -131, J5 = 48.9, J6 = 20.6 }); //Point 6

            FlangeArInte = new List<Joint>();
            FlangeArInte.Add(new Joint { J1 = 0, J2 = 25, J3 = -40, J4 = 0, J5 = 113, J6 = 0 }); //Home
            FlangeArInte.Add(new Joint { J1 = 35, J2 = 35, J3 = -30, J4 = -25, J5 = 110, J6 = 0 }); //Point 1
            FlangeArInte.Add(new Joint { J1 = 40, J2 = 40, J3 = -30, J4 = -45, J5 = 105, J6 = -10 }); //Point 2
            FlangeArInte.Add(new Joint { J1 = 44, J2 = 48, J3 = -17.5, J4 = -96, J5 = 120.6, J6 = -10 }); //Point 3
            FlangeArInte.Add(new Joint { J1 = 57.2, J2 = 48.3, J3 = -55, J4 = -130, J5 = 120, J6 = -55 }); //Point 4
            FlangeArInte.Add(new Joint { J1 = 57.2, J2 = 48.3, J3 = -55, J4 = -107.2, J5 = 45.3, J6 = -30.4 }); //Point 5
            FlangeArInte.Add(new Joint { J1 = 59.4, J2 = 52.3, J3 = -50.7, J4 = -112.3, J5 = 48, J6 = -25.4 }); //Point 6

            //Début de l'écriture 
            //Ecriture des chaque balises et des attributs associés
            String path2 = @"C:\Users\Virtual\Source\Repos\RailsSplicing\BuildProcess.xml";
            xmlWriter = XmlWriter.Create(path2);
            xmlWriter.WriteStartDocument();
            xmlWriter.WriteStartElement("process");

            foreach (Step step in steps)
            {
                xmlWriter.WriteStartElement("Step");
                xmlWriter.WriteAttributeString("id", step.numStep.ToString());
                xmlWriter.WriteAttributeString("Type", "position");
                xmlWriter.WriteAttributeString("C", step.C);
                xmlWriter.WriteAttributeString("Tool", step.Diameter.ToString());
                int numStation = 1;

                foreach (Station station in step.station)
                {
                    xmlWriter.WriteStartElement("Station");
                    xmlWriter.WriteAttributeString("id", numStation.ToString());
                    xmlWriter.WriteAttributeString("Type", "position");
                    xmlWriter.WriteAttributeString("Rail", station.numRail.ToString());
                    xmlWriter.WriteAttributeString("Position", station.position);
                    xmlWriter.WriteAttributeString("Side", station.side);
                    xmlWriter.WriteAttributeString("Points", station.phases.Count.ToString());

                    XmlApproche(station, step); //Ecriture Phase Approche

                    int numPhase = 1;

                    foreach(Phase phase in station.phases)
                    {
                        xmlWriter.WriteStartElement("Phase");
                        xmlWriter.WriteAttributeString("id", (numPhase + 1).ToString());
                        xmlWriter.WriteAttributeString("Type", "position");
                        xmlWriter.WriteAttributeString("Info", "Drill");
                        xmlWriter.WriteAttributeString("FastName", phase.FastenerName);
                        xmlWriter.WriteAttributeString("Mode", "crt");

                        xmlWriter.WriteStartElement("Point");
                        xmlWriter.WriteAttributeString("id", "1");
                        xmlWriter.WriteAttributeString("UT", phase.UT.ToString());
                        xmlWriter.WriteAttributeString("UF", phase.UF.ToString());
                        xmlWriter.WriteAttributeString("X", (phase.X + 673.5).ToString());
                        xmlWriter.WriteAttributeString("Y", (phase.Y - 1332).ToString());
                        xmlWriter.WriteAttributeString("Z", (phase.Z + 493.9).ToString());
                        xmlWriter.WriteAttributeString("W", phase.W.ToString());
                        xmlWriter.WriteAttributeString("P", phase.P.ToString());
                        if (step.C == "Web")
                        {
                            xmlWriter.WriteAttributeString("R", phase.R.ToString());
                        }
                        else if (step.C == "Flange")
                        {
                            if (station.side == "R")
                                xmlWriter.WriteAttributeString("R", (((phase.R) + (Math.Sign(phase.X) * (10 * (numPhase - 1)))).ToString()));
                            else if (station.side == "L")
                                xmlWriter.WriteAttributeString("R", (((phase.R) - (Math.Sign(phase.X) * (10 * (numPhase - 1)))).ToString()));
                        }
                        xmlWriter.WriteAttributeString("E1", phase.E1.ToString());
                        xmlWriter.WriteAttributeString("t4", "0");
                        xmlWriter.WriteAttributeString("t5", "0");
                        xmlWriter.WriteAttributeString("t6", "0");
                        xmlWriter.WriteAttributeString("front", "true");
                        xmlWriter.WriteAttributeString("up", "true");
                        xmlWriter.WriteAttributeString("left", "false");
                        xmlWriter.WriteAttributeString("flip", "true");
                        xmlWriter.WriteAttributeString("type", "linear");
                        xmlWriter.WriteAttributeString("speed", "100");
                        xmlWriter.WriteAttributeString("approx", "fine");
                        xmlWriter.WriteAttributeString("cnt", "100");
                        xmlWriter.WriteEndElement();

                        xmlWriter.WriteEndElement();
                        numPhase++;
                    }

                    XmlClearance(station, step); //Ecriture Phase retour
                    xmlWriter.WriteEndElement();
                    numStation++;
                    numPhase = 1;
                }
                xmlWriter.WriteEndElement();
            }
            xmlWriter.WriteEndElement();
            xmlWriter.WriteEndDocument();
            xmlWriter.Close();
        }

        /***********************************************************************
                          Ecriture Xml de la trajectoire d'approche
        ***********************************************************************/
        private void XmlApproche(Station station, Step step)
        {
            xmlWriter.WriteStartElement("Phase");
            xmlWriter.WriteAttributeString("id", "1");
            xmlWriter.WriteAttributeString("Type", "position");
            xmlWriter.WriteAttributeString("Info", "Approach");
            xmlWriter.WriteAttributeString("Mode", "joint");

            Int32 Signe = 0; //Coté Y+ ou Y-
            List<Joint> movement = null; //Définition d'une liste de "Joint" qui va nous permettre d'écrire en Xml, à cette liste sera attribué une des 6 listes de traj, selon les infos
            String Approx;

            //Ecriture de la liste movement
            if (station.numRail == 1 || station.numRail == 2 || station.numRail == 3)
            {
                Signe = 1;
                if (step.C == "Web")
                {
                    if (station.position == "Back")
                    {
                        movement = WebAr;
                    }
                    else if (station.position == "Front")
                    {
                        movement = WebAv;
                    }
                }

                if (step.C == "Flange")
                {
                    if (station.position == "Front" && station.side == "L")
                    {
                        movement = FlangeAvExte;
                    }
                    else if (station.position == "Front" && station.side == "R")
                    {
                        movement = FlangeAvInte;
                    }
                    else if (station.position == "Back" && station.side == "L")
                    {
                        movement = FlangeArExte;
                    }
                    else if (station.position == "Back" && station.side == "R")
                    {
                        movement = FlangeArInte;
                    }

                }
            }

            else if (station.numRail == 4 || station.numRail == 5 || station.numRail == 6)
            {
                Signe = -1;
                if (step.C == "Web")
                {
                    if (station.position == "Back")
                    {
                        movement = WebAr;
                    }
                    else if (station.position == "Front")
                    {
                        movement = WebAv;
                    }
                }

                if (step.C == "Flange")
                {
                    if (station.position == "Front" && station.side == "L")
                    {
                        movement = FlangeAvInte;
                    }
                    else if (station.position == "Front" && station.side == "R")
                    {
                        movement = FlangeAvExte;
                    }
                    else if (station.position == "Back" && station.side == "L")
                    {
                        movement = FlangeArInte;
                    }
                    else if (station.position == "Back" && station.side == "R")
                    {
                        movement = FlangeArExte;
                    }

                }
            }

            //Ecriture Xml, influence du "signe" sur les Joint d'axe Z
            for (int i = 0; i < movement.Count; i++)
            {
                if (i == movement.Count - 1 || i == movement.Count - 2)
                {
                    Approx = "fine";
                }
                else
                {
                    Approx = "cnt";
                }
                xmlWriter.WriteStartElement("Point");
                xmlWriter.WriteAttributeString("id", (i + 1).ToString());
                xmlWriter.WriteAttributeString("UF", "1");
                xmlWriter.WriteAttributeString("UT", station.phases[0].UT.ToString());
                xmlWriter.WriteAttributeString("X", (Signe * movement[i].J1).ToString());
                xmlWriter.WriteAttributeString("Y", movement[i].J2.ToString());
                xmlWriter.WriteAttributeString("Z", movement[i].J3.ToString());
                xmlWriter.WriteAttributeString("W", (Signe * movement[i].J4).ToString());
                xmlWriter.WriteAttributeString("P", movement[i].J5.ToString());
                xmlWriter.WriteAttributeString("R", (Signe * movement[i].J6).ToString());
                xmlWriter.WriteAttributeString("E1", station.phases[0].E1.ToString());
                xmlWriter.WriteAttributeString("type", "joint");
                xmlWriter.WriteAttributeString("speed", "100");
                xmlWriter.WriteAttributeString("approx", Approx);
                xmlWriter.WriteAttributeString("cnt", "100");
                xmlWriter.WriteEndElement();
            }

            xmlWriter.WriteEndElement();
        }

        /***********************************************************************
                          Ecriture Xml de la trajectoire de retour
        ***********************************************************************/
        private void XmlClearance(Station station, Step step)
        {
            xmlWriter.WriteStartElement("Phase");
            xmlWriter.WriteAttributeString("id", (station.phases.Count+2).ToString());
            xmlWriter.WriteAttributeString("Type", "position");
            xmlWriter.WriteAttributeString("Info", "Clearance");
            xmlWriter.WriteAttributeString("Mode", "joint");

            Int32 Signe = 0; //Coté Y+ ou Y-
            List<Joint> movement = null; //Définition d'une liste de "Joint" qui va nous permettre d'écrire en Xml, à cette liste sera attribué une des 6 listes de traj, selon les infos
            String Approx;

            //Ecriture de la liste movement
            if (station.numRail == 1 || station.numRail == 2 || station.numRail == 3)
            {
                Signe = 1;
                if (step.C == "Web")
                {
                    if (station.position == "Back")
                    {
                        movement = WebAr;
                    }
                    else if (station.position == "Front")
                    {
                        movement = WebAv;
                    }
                }

                if (step.C == "Flange")
                {
                    if (station.position == "Front" && station.side == "L")
                    {
                        movement = FlangeAvExte;
                    }
                    else if (station.position == "Front" && station.side == "R")
                    {
                        movement = FlangeAvInte;
                    }
                    else if (station.position == "Back" && station.side == "L")
                    {
                        movement = FlangeArExte;
                    }
                    else if (station.position == "Back" && station.side == "R")
                    {
                        movement = FlangeArInte;
                    }

                }
            }

            else if (station.numRail == 4 || station.numRail == 5 || station.numRail == 6)
            {
                Signe = -1;
                if (step.C == "Web")
                {
                    if (station.position == "Back")
                    {
                        movement = WebAr;
                    }
                    else if (station.position == "Front")
                    {
                        movement = WebAv;
                    }
                }

                if (step.C == "Flange")
                {
                    if (station.position == "Front" && station.side == "L")
                    {
                        movement = FlangeAvInte;
                    }
                    else if (station.position == "Front" && station.side == "R")
                    {
                        movement = FlangeAvExte;
                    }
                    else if (station.position == "Back" && station.side == "L")
                    {
                        movement = FlangeArInte;
                    }
                    else if (station.position == "Back" && station.side == "R")
                    {
                        movement = FlangeArExte;
                    }

                }
            }

            //Ecriture Xml, influence du "signe" sur les Joint d'axe Z
            //Inversion des points : On commence par le dernier de la liste 
            for (int i = movement.Count - 1; i >= 0; i--)
            {
                if (i == movement.Count - 1 || i == movement.Count - 2)
                {
                    Approx = "fine";
                }
                else
                {
                    Approx = "cnt";
                }
                xmlWriter.WriteStartElement("Point");
                xmlWriter.WriteAttributeString("id", (movement.Count - i).ToString());
                xmlWriter.WriteAttributeString("UF", "1");
                xmlWriter.WriteAttributeString("UT", station.phases[0].UT.ToString());
                xmlWriter.WriteAttributeString("X", (Signe * movement[i].J1).ToString());
                xmlWriter.WriteAttributeString("Y", movement[i].J2.ToString());
                xmlWriter.WriteAttributeString("Z", movement[i].J3.ToString());
                xmlWriter.WriteAttributeString("W", (Signe * movement[i].J4).ToString());
                xmlWriter.WriteAttributeString("P", movement[i].J5.ToString());
                xmlWriter.WriteAttributeString("R", (Signe * movement[i].J6).ToString());
                xmlWriter.WriteAttributeString("E1", station.phases[0].E1.ToString());
                xmlWriter.WriteAttributeString("type", "joint");
                xmlWriter.WriteAttributeString("speed", "100");
                xmlWriter.WriteAttributeString("approx", Approx);
                xmlWriter.WriteAttributeString("cnt", "100");
                xmlWriter.WriteEndElement();
            }

            xmlWriter.WriteEndElement();
        }

        /***********************************************************************
                       Trouve les coordonnées Y des Rails (6)
        ***********************************************************************/
        private List<Double> DefineRails(List<CatiaData> liste)
        {
            List<Double> listeRails = new List<Double>();

            foreach (CatiaData data in liste)
            {
                double Y;
                Y = data.YValue;
                if ((int)data.YDir == 1 || (int)data.YDir == -1)
                {
                    double HD = data.Depth;
                    if (HD < 5.81 && HD > 5.79)
                        HD = 5.4;
                    if (!listeRails.Contains(Y + Math.Sign(data.YDir) * HD / 2))
                    {
                        listeRails.Add(Y + Math.Sign(data.YDir) * HD / 2);
                    }
                }
            }
            triRails(listeRails);
            return listeRails;
        }

        /***********************************************************************
                           Tri les Rails selon Y décroissant
        ***********************************************************************/
        private void triRails(List<Double> Rails)
        {
            int ndebut = 0;
            int nfin = Rails.Count - 1;
            while (ndebut < nfin)
            {
                int debut = ndebut;
                int fin = nfin;
                ndebut = Rails.Count;
                for (int i = debut; i < fin; i++)
                {
                    if (Rails[i] < Rails[i+1])
                    {
                        Double trans = Rails[i];
                        Rails[i] = Rails[i + 1];
                        Rails[i + 1] = trans;
                        if (i < ndebut)
                        {
                            ndebut = i - 1;
                            if (ndebut < 0)
                            {
                                ndebut = 0;
                            }
                        }
                        else if (i > nfin)
                        {
                            nfin = i + 1;
                        }
                    }
                }
            }
        }
    }
}
