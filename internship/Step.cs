using System;
using System.Collections.Generic;
using System.Text;

namespace DataAnalyser
{
    class Step
    {
        public static Int32 CptStep = 0;
        public Int32 numStep;
        public String C;
        public Double Diameter;
        public List<Station> station;

        public Step(String C, Double diameter)
        {
            CptStep++;
            this.numStep = CptStep;
            this.C = C;
            this.Diameter = diameter;
            this.station = new List<Station>();
        }
    }
}
