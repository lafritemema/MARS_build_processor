using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace DataAnalyser
{
    class Point
    {
        public String FastenerName;
        public String C;
        public Double Diameter;
        public Int32 Rail;
        public String Position;
        public String Side;
        public Double X;
        public Double Y;
        public Double Z;
        public Double Depth;
        public Double Ydir;

        public Point(Form1.CatiaData pnt, List<Double> YRails)
        {
            this.FastenerName = pnt.Name;
            this.C = SetC(pnt.YDir, pnt.ZDir);
            this.Diameter = pnt.Diameter;
            this.Rail = SetRail(pnt.YValue, YRails);
            this.Position = SetPos(pnt.XValue);
            this.Side = SetSide(pnt.YValue, this.Rail, YRails);
            this.X = pnt.XValue;
            this.Y = pnt.YValue;
            this.Z = pnt.ZValue;
            if (pnt.Depth < 5.81 && pnt.Depth > 5.79)
                this.Depth = 5.4;
            else
                this.Depth = pnt.Depth;
            this.Ydir = pnt.YDir;
        }

        public String SetC(Double Yd, Double Zd)
        {
            if (Yd == 1 || Yd == -1)
                return "Web";
            else if ((Zd == 1 || Zd == -1))
                return "Flange";
            return null;
        }

        public String SetPos(Double X)
        {

            if (X > 0)
                return "Front";
            else
                return "Back";
        }

        public String SetSide(Double Y, Int32 Rail, List<Double> YRails)
        {
            if (C == "Flange")
            {
                String res;

                if (Y > YRails[Rail-1])
                    res = "L";
                else
                    res = "R";
                return res;
            }
            return null;
        }

        public Int32 SetRail(Double Y, List<Double> YRails)
        {
            //On pourrait demander les pos yrails à l'opérateur et faire Yrail-50 < Y < Yrail+50
            int res = 0;
            int numRail = 0;
            foreach(Double Rail in YRails)
            {
                numRail++;
                if (Y < Rail + 50 && Y > Rail - 50)
                    res = numRail;
            }
            return res;
        }
    }
}
