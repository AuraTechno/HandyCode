"""
Логотип HandyCode для командной строки
"""

import sys
from .utils import Colors, supports_color

def get_logo() -> str:
    if not supports_color():
        return get_logo_plain()

    C = Colors
    logo = f"""
{C.CYAN}╔═════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                                 ║
║  {C.YELLOW}██╗  ██╗{C.CYAN}  {C.GREEN}█████╗{C.CYAN}    {C.BLUE}███╗   ██╗{C.CYAN}  {C.MAGENTA}██████╗{C.CYAN}   {C.RED}██╗   ██╗{C.CYAN}    {C.WHITE}██████╗{C.CYAN}   {C.GREEN}███████╗{C.CYAN}  {C.BLUE}██████╗{C.CYAN}    {C.MAGENTA}███████╗{C.CYAN} ║
║  {C.YELLOW}██║  ██║{C.CYAN}  {C.GREEN}██╔══██╗{C.CYAN}  {C.BLUE}████╗  ██║{C.CYAN}  {C.MAGENTA}██╔══██╗{C.CYAN}  {C.RED}╚██╗ ██╔╝{C.CYAN}    {C.WHITE}██╔════╝{C.CYAN} {C.GREEN}██╔════██╗{C.CYAN}  {C.BLUE}██╔══██╗{C.CYAN}  {C.MAGENTA}██╔════╝{C.CYAN} ║
║  {C.YELLOW}███████║{C.CYAN}  {C.GREEN}███████║{C.CYAN}  {C.BLUE}██╔██╗ ██║{C.CYAN}  {C.MAGENTA}██║  ██║{C.CYAN}   {C.RED}╚████╔╝{C.CYAN}     {C.WHITE}██║{C.CYAN}     {C.GREEN}██║      ██║{C.CYAN} {C.BLUE}██║  ██║{C.CYAN}  {C.MAGENTA}█████╗{C.CYAN}   ║
║  {C.YELLOW}██╔══██║{C.CYAN}  {C.GREEN}██╔══██║{C.CYAN}  {C.BLUE}██║╚██╗██║{C.CYAN}  {C.MAGENTA}██║  ██║{C.CYAN}    {C.RED}╚██╔╝{C.CYAN}      {C.WHITE}██║{C.CYAN}      {C.GREEN}██║    ██║{C.CYAN}  {C.BLUE}██║  ██║{C.CYAN}  {C.MAGENTA}██╔══╝{C.CYAN}   ║
║  {C.YELLOW}██║  ██║{C.CYAN}  {C.GREEN}██║  ██║{C.CYAN}  {C.BLUE}██║ ╚████║{C.CYAN}  {C.MAGENTA}██████╔╝{C.CYAN}     {C.RED}██║{C.CYAN}       {C.WHITE}╚██████╗{C.CYAN}  {C.GREEN}███████╔╝{C.CYAN}  {C.BLUE}██████╔╝{C.CYAN}  {C.MAGENTA}███████╗{C.CYAN} ║
║  {C.YELLOW}╚═╝  ╚═╝{C.CYAN}  {C.GREEN}╚═╝  ╚═╝{C.CYAN}  {C.BLUE}╚═╝  ╚═══╝{C.CYAN}  {C.MAGENTA}╚═════╝{C.CYAN}      {C.RED}╚═╝{C.CYAN}       {C.WHITE} ╚═════╝{C.CYAN}   {C.GREEN}╚═════╝{C.CYAN}   {C.BLUE}╚═════╝{C.CYAN}   {C.MAGENTA}╚══════╝{C.CYAN} ║
║                                                                                                 ║
║  {C.WHITE}AI Ассистент для разработки{C.CYAN}                                                                    ║
║        {C.WHITE}Prod. by AURA Tec.{C.CYAN}                                                                       ║
║                                                                                                 ║
╚═════════════════════════════════════════════════════════════════════════════════════════════════╝{C.RESET}
"""
    return logo

def get_logo_plain() -> str:
    return r"""
╔═════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                                 ║
║  ██╗  ██╗  █████╗  ███╗   ██╗  ██████╗  ██╗   ██╗     ██████╗  ███████╗  ██████╗  ███████╗ ║
║  ██║  ██║  ██╔══██╗ ████╗  ██║  ██╔══██╗ ╚██╗ ██╔╝     ██╔════╝  ██╔════██╗ ██╔══██╗ ██╔════╝ ║
║  ███████║  ███████║ ██╔██╗ ██║  ██║  ██║  ╚████╔╝      ██║       ██║      ██║ ██║  ██║ █████╗   ║
║  ██╔══██║  ██╔══██║ ██║╚██╗██║  ██║  ██║   ╚██╔╝       ██║       ██║    ██║  ██║  ██║ ██╔══╝   ║
║  ██║  ██║  ██║  ██║ ██║ ╚████║  ██████╔╝    ██║        ╚██████╗  ███████╔╝  ██████╔╝ ███████╗ ║
║  ╚═╝  ╚═╝  ╚═╝  ╚═╝ ╚═╝  ╚═══╝  ╚═════╝     ╚═╝         ╚═════╝  ╚═════╝   ╚═════╝  ╚══════╝ ║
║                                                                                                 ║
║              AI Ассистент для разработки                                                       ║
║                    Prod. by AURA Tec.                                                          ║
║                                                                                                 ║
╚═════════════════════════════════════════════════════════════════════════════════════════════════╝
"""

def get_small_logo() -> str:
    if not supports_color():
        return "HandyCode v2.1.3"
    C = Colors
    return f"{C.CYAN}HandyCode{C.RESET} {C.WHITE}v2.1.3{C.RESET} – {C.GREEN}AI Ассистент{C.RESET}  {C.BRIGHT_BLACK}Prod. by AURA Tec.{C.RESET}"

def get_install_logo() -> str:
    if not supports_color():
        return get_logo_plain()
    C = Colors
    return f"""
{C.CYAN}╔═════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                                 ║
║  {C.YELLOW}██╗  ██╗{C.CYAN}  {C.GREEN}█████╗{C.CYAN}    {C.BLUE}███╗   ██╗{C.CYAN}  {C.MAGENTA}██████╗{C.CYAN}   {C.RED}██╗   ██╗{C.CYAN}    {C.WHITE}██████╗{C.CYAN}   {C.GREEN}███████╗{C.CYAN}  {C.BLUE}██████╗{C.CYAN}    {C.MAGENTA}███████╗{C.CYAN} ║
║  {C.YELLOW}██║  ██║{C.CYAN}  {C.GREEN}██╔══██╗{C.CYAN}  {C.BLUE}████╗  ██║{C.CYAN}  {C.MAGENTA}██╔══██╗{C.CYAN}  {C.RED}╚██╗ ██╔╝{C.CYAN}    {C.WHITE}██╔════╝{C.CYAN} {C.GREEN}██╔════██╗{C.CYAN}  {C.BLUE}██╔══██╗{C.CYAN}  {C.MAGENTA}██╔════╝{C.CYAN} ║
║  {C.YELLOW}███████║{C.CYAN}  {C.GREEN}███████║{C.CYAN}  {C.BLUE}██╔██╗ ██║{C.CYAN}  {C.MAGENTA}██║  ██║{C.CYAN}   {C.RED}╚████╔╝{C.CYAN}     {C.WHITE}██║{C.CYAN}     {C.GREEN}██║      ██║{C.CYAN} {C.BLUE}██║  ██║{C.CYAN}  {C.MAGENTA}█████╗{C.CYAN}   ║
║  {C.YELLOW}██╔══██║{C.CYAN}  {C.GREEN}██╔══██║{C.CYAN}  {C.BLUE}██║╚██╗██║{C.CYAN}  {C.MAGENTA}██║  ██║{C.CYAN}    {C.RED}╚██╔╝{C.CYAN}      {C.WHITE}██║{C.CYAN}      {C.GREEN}██║    ██║{C.CYAN}  {C.BLUE}██║  ██║{C.CYAN}  {C.MAGENTA}██╔══╝{C.CYAN}   ║
║  {C.YELLOW}██║  ██║{C.CYAN}  {C.GREEN}██║  ██║{C.CYAN}  {C.BLUE}██║ ╚████║{C.CYAN}  {C.MAGENTA}██████╔╝{C.CYAN}     {C.RED}██║{C.CYAN}       {C.WHITE}╚██████╗{C.CYAN}  {C.GREEN}███████╔╝{C.CYAN}  {C.BLUE}██████╔╝{C.CYAN}  {C.MAGENTA}███████╗{C.CYAN} ║
║  {C.YELLOW}╚═╝  ╚═╝{C.CYAN}  {C.GREEN}╚═╝  ╚═╝{C.CYAN}  {C.BLUE}╚═╝  ╚═══╝{C.CYAN}  {C.MAGENTA}╚═════╝{C.CYAN}      {C.RED}╚═╝{C.CYAN}       {C.WHITE} ╚═════╝{C.CYAN}   {C.GREEN}╚═════╝{C.CYAN}   {C.BLUE}╚═════╝{C.CYAN}   {C.MAGENTA}╚══════╝{C.CYAN} ║
║                                                                                                 ║
║                            {C.WHITE}УСТАНОВКА HANDYCODE{C.CYAN}                                             ║
║  {C.WHITE}AI Ассистент для разработки{C.CYAN}                                                                    ║
║        {C.WHITE}Prod. by AURA Tec.{C.CYAN}                                                                       ║
║                                                                                                 ║
╚═════════════════════════════════════════════════════════════════════════════════════════════════╝{C.RESET}
"""