using System;
using System.Collections.Generic;
using System.Linq;
using System.Security;
using System.Text;
using System.Threading.Tasks;

namespace DataAnalyser
{
    class Phase
    {
        public String FastenerName;
        public int UT;
        public int UF;
        public double X;
        public double Y;
        public double Z;
        public double W;
        public double P;
        public double R;
        public double E1;
        //public int t4;
        //public int t5;
        //public int t6;
        //public bool front;
        //public bool flip;
        //public bool up;
        //public bool left;
        //public String type;
        //public int speed;
        //public String approx;
        //public int cnt;

        public Phase(Point p)
        {
            FastenerName = p.FastenerName;
            if (p.C == "Web")
            {
                UT = 1;
                W = Math.Sign(p.Y) * 90;
                P = -90;
                R = 0;
                Double offset = 0;

                //On pourrait demander le Y de la matrice de transition
                if (p.Position == "Front")
                {
                    offset = 700;
                }
                else if (p.Position == "Back")
                {
                    offset = 800;
                }
                E1 = (Form1.YRail1 - (p.Y + Math.Sign(p.Ydir) * p.Depth / 2)) + (Math.Sign(p.Y) * offset);
                Y = 2 * E1 + (p.Y + Math.Sign(p.Ydir) * p.Depth / 2);
            }

            else if (p.C == "Flange")
            {
                UT = 2;
                W = -180;
                P = 0;
                if (p.Side == "R")
                    R = -90;
                else if (p.Side == "L")
                    R = 90;

                Double ecart; //on pourrait les demander à l'opérateur
                if (p.Rail == 1 || p.Rail == 2 || p.Rail == 5 || p.Rail == 6)
                    ecart = Form1.Flange_Offset1;
                else
                    ecart = Form1.Flange_Offset2;

                Double offset = 0;
                Int32 signe = 0;

                if (p.Side == "L")
                {
                    signe = -1;
                    if (p.Position == "Front")
                    {
                        if (p.Rail == 1 || p.Rail == 2 || p.Rail == 3)
                            offset = 250;
                        else
                            offset = 500;
                    }
                    else if (p.Position == "Back")
                    {
                        if (p.Rail == 1 || p.Rail == 2 || p.Rail == 3)
                            offset = 350;
                        else
                            offset = 600;
                    }
                }
                else if (p.Side == "R")
                {
                    signe = 1;
                    if (p.Position == "Front")
                    {
                        if (p.Rail == 1 || p.Rail == 2 || p.Rail == 3)
                            offset = 500;
                        else
                            offset = 250;
                    }
                    else if (p.Position == "Back")
                    {
                        if (p.Rail == 1 || p.Rail == 2 || p.Rail == 3)
                            offset = 600;
                        else
                            offset = 350;
                    }
                }

                E1 = Form1.YRail1 - (p.Y + signe * ecart) + Math.Sign(p.Y) * offset;
                Y = 2 * E1 + p.Y;
            }
            UF = 1;
            //On pourrait demander à l'opérateur les valeurs X et Y de la matrice de Transition
            X = p.X;
            Z = p.Z;

        }
    }
}
