using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using System.Windows.Forms;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Text;
using System.Threading;
using System.Xml.Serialization;
using System.IO;
using System.Collections;
using System.Xml;
using System.Security.Cryptography.X509Certificates;
using System.Drawing.Text;
using System.Diagnostics;
using System.Runtime.CompilerServices;

namespace DataAnalyser
{
    static class Program
    {
    [STAThread]
        static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new Form1());
        }
    }
}
