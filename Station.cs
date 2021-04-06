using System;
using System.Collections.Generic;
using System.Text;
using System.Threading;

namespace DataAnalyser
{
    class Station
    {
        public List<Phase> phases;
        public Int32 numRail;
        public String position;
        public String side;

        public Station(int num, String pos)
        {
            this.numRail = num;
            this.position = pos;
            phases = new List<Phase>();
        }

        public Station(int num, String pos, String Side)
        {
            this.numRail = num;
            this.position = pos;
            this.side = Side;
            phases = new List<Phase>();
        }

    }

}
