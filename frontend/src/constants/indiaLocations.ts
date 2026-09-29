/**
 * Indian states/UTs and their districts.
 * Used for signup form dropdowns.
 * Alphabetically ordered states; districts alphabetically ordered per state.
 */

export interface StateEntry {
  name: string;
  districts: string[];
}

export const INDIA_STATES: StateEntry[] = [
  {
    name: "Andaman and Nicobar Islands",
    districts: ["Nicobar", "North and Middle Andaman", "South Andaman"],
  },
  {
    name: "Andhra Pradesh",
    districts: [
      "Alluri Sitharama Raju", "Anakapalli", "Anantapur", "Annamayya",
      "Bapatla", "Chittoor", "Eluru", "East Godavari", "Guntur", "Kakinada",
      "Konaseema", "Krishna", "Kurnool", "Manyam", "NTR", "Nandyal",
      "Nellore", "Palnadu", "Prakasam", "Sri Potti Sri Ramulu Nellore",
      "Sri Sathya Sai", "Srikakulam", "Tirupati", "Visakhapatnam",
      "Vizianagaram", "West Godavari", "YSR Kadapa",
    ],
  },
  {
    name: "Arunachal Pradesh",
    districts: [
      "Anjaw", "Changlang", "Dibang Valley", "East Kameng", "East Siang",
      "Kamle", "Kra Daadi", "Kurung Kumey", "Lepa Rada", "Lohit",
      "Longding", "Lower Dibang Valley", "Lower Siang", "Lower Subansiri",
      "Namsai", "Pakke-Kessang", "Papum Pare", "Shi Yomi", "Siang",
      "Tawang", "Tirap", "Upper Dibang Valley", "Upper Siang", "Upper Subansiri",
      "West Kameng", "West Siang",
    ],
  },
  {
    name: "Assam",
    districts: [
      "Baksa", "Barpeta", "Biswanath", "Bongaigaon", "Cachar", "Charaideo",
      "Chirang", "Darrang", "Dhemaji", "Dhubri", "Dibrugarh", "Dima Hasao",
      "Goalpara", "Golaghat", "Hailakandi", "Hojai", "Jorhat", "Kamrup",
      "Kamrup Metropolitan", "Karbi Anglong", "Karimganj", "Kokrajhar",
      "Lakhimpur", "Majuli", "Morigaon", "Nagaon", "Nalbari", "Sivasagar",
      "Sonitpur", "South Salmara-Mankachar", "Tinsukia", "Udalguri",
      "West Karbi Anglong",
    ],
  },
  {
    name: "Bihar",
    districts: [
      "Araria", "Arwal", "Aurangabad", "Banka", "Begusarai", "Bhagalpur",
      "Bhojpur", "Buxar", "Darbhanga", "East Champaran", "Gaya", "Gopalganj",
      "Jamui", "Jehanabad", "Kaimur", "Katihar", "Khagaria", "Kishanganj",
      "Lakhisarai", "Madhepura", "Madhubani", "Munger", "Muzaffarpur",
      "Nalanda", "Nawada", "Patna", "Purnia", "Rohtas", "Saharsa",
      "Samastipur", "Saran", "Sheikhpura", "Sheohar", "Sitamarhi", "Siwan",
      "Supaul", "Vaishali", "West Champaran",
    ],
  },
  {
    name: "Chandigarh",
    districts: ["Chandigarh"],
  },
  {
    name: "Chhattisgarh",
    districts: [
      "Balod", "Baloda Bazar", "Balrampur", "Bastar", "Bemetara", "Bijapur",
      "Bilaspur", "Dantewada", "Dhamtari", "Durg", "Gariaband", "Gaurela-Pendra-Marwahi",
      "Janjgir-Champa", "Jashpur", "Kabirdham", "Kanker", "Khairagarh",
      "Kondagaon", "Korba", "Koriya", "Mahasamund", "Manendragarh",
      "Mohla-Manpur", "Mungeli", "Narayanpur", "Raigarh", "Raipur",
      "Rajnandgaon", "Sakti", "Sarangarh-Bilaigarh", "Sukma", "Surajpur",
      "Surguja",
    ],
  },
  {
    name: "Dadra and Nagar Haveli and Daman and Diu",
    districts: ["Dadra and Nagar Haveli", "Daman", "Diu"],
  },
  {
    name: "Delhi",
    districts: [
      "Central Delhi", "East Delhi", "New Delhi", "North Delhi",
      "North East Delhi", "North West Delhi", "Shahdara", "South Delhi",
      "South East Delhi", "South West Delhi", "West Delhi",
    ],
  },
  {
    name: "Goa",
    districts: ["North Goa", "South Goa"],
  },
  {
    name: "Gujarat",
    districts: [
      "Ahmedabad", "Amreli", "Anand", "Aravalli", "Banaskantha", "Bharuch",
      "Bhavnagar", "Botad", "Chhota Udaipur", "Dahod", "Dang",
      "Devbhumi Dwarka", "Gandhinagar", "Gir Somnath", "Jamnagar", "Junagadh",
      "Kheda", "Kutch", "Mahisagar", "Mehsana", "Morbi", "Narmada",
      "Navsari", "Panchmahal", "Patan", "Porbandar", "Rajkot", "Sabarkantha",
      "Surat", "Surendranagar", "Tapi", "Vadodara", "Valsad",
    ],
  },
  {
    name: "Haryana",
    districts: [
      "Ambala", "Bhiwani", "Charkhi Dadri", "Faridabad", "Fatehabad",
      "Gurugram", "Hisar", "Jhajjar", "Jind", "Kaithal", "Karnal",
      "Kurukshetra", "Mahendragarh", "Nuh", "Palwal", "Panchkula",
      "Panipat", "Rewari", "Rohtak", "Sirsa", "Sonipat", "Yamunanagar",
    ],
  },
  {
    name: "Himachal Pradesh",
    districts: [
      "Bilaspur", "Chamba", "Hamirpur", "Kangra", "Kinnaur", "Kullu",
      "Lahaul and Spiti", "Mandi", "Shimla", "Sirmaur", "Solan", "Una",
    ],
  },
  {
    name: "Jammu and Kashmir",
    districts: [
      "Anantnag", "Bandipora", "Baramulla", "Budgam", "Doda", "Ganderbal",
      "Jammu", "Kathua", "Kishtwar", "Kulgam", "Kupwara", "Poonch",
      "Pulwama", "Rajouri", "Ramban", "Reasi", "Samba", "Shopian",
      "Srinagar", "Udhampur",
    ],
  },
  {
    name: "Jharkhand",
    districts: [
      "Bokaro", "Chatra", "Deoghar", "Dhanbad", "Dumka", "East Singhbhum",
      "Garhwa", "Giridih", "Godda", "Gumla", "Hazaribagh", "Jamtara",
      "Khunti", "Koderma", "Latehar", "Lohardaga", "Pakur", "Palamu",
      "Ramgarh", "Ranchi", "Sahibganj", "Seraikela Kharsawan", "Simdega",
      "West Singhbhum",
    ],
  },
  {
    name: "Karnataka",
    districts: [
      "Bagalkot", "Ballari", "Belagavi", "Bengaluru Rural", "Bengaluru Urban",
      "Bidar", "Chamarajanagar", "Chikkaballapur", "Chikkamagaluru",
      "Chitradurga", "Dakshina Kannada", "Davanagere", "Dharwad",
      "Gadag", "Hassan", "Haveri", "Kalaburagi", "Kodagu", "Kolar",
      "Koppal", "Mandya", "Mysuru", "Raichur", "Ramanagara", "Shivamogga",
      "Tumakuru", "Udupi", "Uttara Kannada", "Vijayapura", "Yadgir",
    ],
  },
  {
    name: "Kerala",
    districts: [
      "Alappuzha", "Ernakulam", "Idukki", "Kannur", "Kasaragod",
      "Kollam", "Kottayam", "Kozhikode", "Malappuram", "Palakkad",
      "Pathanamthitta", "Thiruvananthapuram", "Thrissur", "Wayanad",
    ],
  },
  {
    name: "Ladakh",
    districts: ["Kargil", "Leh"],
  },
  {
    name: "Lakshadweep",
    districts: ["Lakshadweep"],
  },
  {
    name: "Madhya Pradesh",
    districts: [
      "Agar Malwa", "Alirajpur", "Anuppur", "Ashoknagar", "Balaghat",
      "Barwani", "Betul", "Bhind", "Bhopal", "Burhanpur", "Chhatarpur",
      "Chhindwara", "Damoh", "Datia", "Dewas", "Dhar", "Dindori",
      "Guna", "Gwalior", "Harda", "Hoshangabad", "Indore", "Jabalpur",
      "Jhabua", "Katni", "Khandwa", "Khargone", "Mandla", "Mandsaur",
      "Morena", "Narsinghpur", "Neemuch", "Niwari", "Panna", "Raisen",
      "Rajgarh", "Ratlam", "Rewa", "Sagar", "Satna", "Sehore",
      "Seoni", "Shahdol", "Shajapur", "Sheopur", "Shivpuri", "Sidhi",
      "Singrauli", "Tikamgarh", "Ujjain", "Umaria", "Vidisha",
    ],
  },
  {
    name: "Maharashtra",
    districts: [
      "Ahmednagar", "Akola", "Amravati", "Aurangabad", "Beed", "Bhandara",
      "Buldhana", "Chandrapur", "Dhule", "Gadchiroli", "Gondia", "Hingoli",
      "Jalgaon", "Jalna", "Kolhapur", "Latur", "Mumbai City", "Mumbai Suburban",
      "Nagpur", "Nanded", "Nandurbar", "Nashik", "Osmanabad", "Palghar",
      "Parbhani", "Pune", "Raigad", "Ratnagiri", "Sangli", "Satara",
      "Sindhudurg", "Solapur", "Thane", "Wardha", "Washim", "Yavatmal",
    ],
  },
  {
    name: "Manipur",
    districts: [
      "Bishnupur", "Chandel", "Churachandpur", "Imphal East", "Imphal West",
      "Jiribam", "Kakching", "Kamjong", "Kangpokpi", "Noney", "Pherzawl",
      "Senapati", "Tamenglong", "Tengnoupal", "Thoubal", "Ukhrul",
    ],
  },
  {
    name: "Meghalaya",
    districts: [
      "East Garo Hills", "East Jaintia Hills", "East Khasi Hills",
      "Eastern West Khasi Hills", "North Garo Hills", "Ri Bhoi",
      "South Garo Hills", "South West Garo Hills", "South West Khasi Hills",
      "West Garo Hills", "West Jaintia Hills", "West Khasi Hills",
    ],
  },
  {
    name: "Mizoram",
    districts: [
      "Aizawl", "Champhai", "Hnahthial", "Khawzawl", "Kolasib",
      "Lawngtlai", "Lunglei", "Mamit", "Saiha", "Saitual", "Serchhip",
    ],
  },
  {
    name: "Nagaland",
    districts: [
      "Chumoukedima", "Dimapur", "Kiphire", "Kohima", "Longleng",
      "Mokokchung", "Mon", "Niuland", "Noklak", "Peren", "Phek",
      "Shamator", "Tseminyü", "Tuensang", "Wokha", "Zunheboto",
    ],
  },
  {
    name: "Odisha",
    districts: [
      "Angul", "Balangir", "Balasore", "Bargarh", "Bhadrak", "Boudh",
      "Cuttack", "Deogarh", "Dhenkanal", "Gajapati", "Ganjam", "Jagatsinghpur",
      "Jajpur", "Jharsuguda", "Kalahandi", "Kandhamal", "Kendrapara",
      "Kendujhar", "Khordha", "Koraput", "Malkangiri", "Mayurbhanj",
      "Nabarangpur", "Nayagarh", "Nuapada", "Puri", "Rayagada",
      "Sambalpur", "Sonepur", "Sundargarh",
    ],
  },
  {
    name: "Puducherry",
    districts: ["Karaikal", "Mahe", "Puducherry", "Yanam"],
  },
  {
    name: "Punjab",
    districts: [
      "Amritsar", "Barnala", "Bathinda", "Faridkot", "Fatehgarh Sahib",
      "Fazilka", "Ferozepur", "Gurdaspur", "Hoshiarpur", "Jalandhar",
      "Kapurthala", "Ludhiana", "Malerkotla", "Mansa", "Moga",
      "Mohali", "Muktsar", "Nawanshahr", "Pathankot", "Patiala",
      "Rupnagar", "Sangrur", "Tarn Taran",
    ],
  },
  {
    name: "Rajasthan",
    districts: [
      "Ajmer", "Alwar", "Banswara", "Baran", "Barmer", "Bharatpur",
      "Bhilwara", "Bikaner", "Bundi", "Chittorgarh", "Churu", "Dausa",
      "Dholpur", "Dungarpur", "Hanumangarh", "Jaipur", "Jaisalmer",
      "Jalore", "Jhalawar", "Jhunjhunu", "Jodhpur", "Karauli", "Kota",
      "Nagaur", "Pali", "Pratapgarh", "Rajsamand", "Sawai Madhopur",
      "Sikar", "Sirohi", "Sri Ganganagar", "Tonk", "Udaipur",
    ],
  },
  {
    name: "Sikkim",
    districts: ["East Sikkim", "North Sikkim", "Pakyong", "Soreng", "South Sikkim", "West Sikkim"],
  },
  {
    name: "Tamil Nadu",
    districts: [
      "Ariyalur", "Chengalpattu", "Chennai", "Coimbatore", "Cuddalore",
      "Dharmapuri", "Dindigul", "Erode", "Kallakurichi", "Kanchipuram",
      "Kanyakumari", "Karur", "Krishnagiri", "Madurai", "Mayiladuthurai",
      "Nagapattinam", "Namakkal", "Nilgiris", "Perambalur", "Pudukkottai",
      "Ramanathapuram", "Ranipet", "Salem", "Sivaganga", "Tenkasi",
      "Thanjavur", "Theni", "Thoothukudi", "Tiruchirappalli", "Tirunelveli",
      "Tirupattur", "Tiruvallur", "Tiruvannamalai", "Tiruvarur", "Vellore",
      "Viluppuram", "Virudhunagar",
    ],
  },
  {
    name: "Telangana",
    districts: [
      "Adilabad", "Bhadradri Kothagudem", "Hanamkonda", "Hyderabad",
      "Jagtial", "Jangaon", "Jayashankar Bhupalpally", "Jogulamba Gadwal",
      "Kamareddy", "Karimnagar", "Khammam", "Kumuram Bheem Asifabad",
      "Mahabubabad", "Mahabubnagar", "Mancherial", "Medak", "Medchal-Malkajgiri",
      "Mulugu", "Nagarkurnool", "Nalgonda", "Narayanpet", "Nirmal",
      "Nizamabad", "Peddapalli", "Rajanna Sircilla", "Rangareddy",
      "Sangareddy", "Siddipet", "Suryapet", "Vikarabad", "Wanaparthy",
      "Warangal", "Yadadri Bhuvanagiri",
    ],
  },
  {
    name: "Tripura",
    districts: [
      "Dhalai", "Gomati", "Khowai", "North Tripura", "Sepahijala",
      "South Tripura", "Sipahijala", "Unakoti", "West Tripura",
    ],
  },
  {
    name: "Uttar Pradesh",
    districts: [
      "Agra", "Aligarh", "Ambedkar Nagar", "Amethi", "Amroha", "Auraiya",
      "Ayodhya", "Azamgarh", "Baghpat", "Bahraich", "Ballia", "Balrampur",
      "Banda", "Barabanki", "Bareilly", "Basti", "Bhadohi", "Bijnor",
      "Budaun", "Bulandshahr", "Chandauli", "Chitrakoot", "Deoria", "Etah",
      "Etawah", "Farrukhabad", "Fatehpur", "Firozabad", "Gautam Buddha Nagar",
      "Ghaziabad", "Ghazipur", "Gonda", "Gorakhpur", "Hamirpur", "Hapur",
      "Hardoi", "Hathras", "Jalaun", "Jaunpur", "Jhansi", "Kannauj",
      "Kanpur Dehat", "Kanpur Nagar", "Kasganj", "Kaushambi", "Kushinagar",
      "Lakhimpur Kheri", "Lalitpur", "Lucknow", "Maharajganj", "Mahoba",
      "Mainpuri", "Mathura", "Mau", "Meerut", "Mirzapur", "Moradabad",
      "Muzaffarnagar", "Pilibhit", "Pratapgarh", "Prayagraj", "Rae Bareli",
      "Rampur", "Saharanpur", "Sambhal", "Sant Kabir Nagar", "Shahjahanpur",
      "Shamli", "Shravasti", "Siddharthnagar", "Sitapur", "Sonbhadra",
      "Sultanpur", "Unnao", "Varanasi",
    ],
  },
  {
    name: "Uttarakhand",
    districts: [
      "Almora", "Bageshwar", "Chamoli", "Champawat", "Dehradun", "Haridwar",
      "Nainital", "Pauri Garhwal", "Pithoragarh", "Rudraprayag",
      "Tehri Garhwal", "Udham Singh Nagar", "Uttarkashi",
    ],
  },
  {
    name: "West Bengal",
    districts: [
      "Alipurduar", "Bankura", "Birbhum", "Cooch Behar", "Dakshin Dinajpur",
      "Darjeeling", "Hooghly", "Howrah", "Jalpaiguri", "Jhargram",
      "Kalimpong", "Kolkata", "Malda", "Murshidabad", "Nadia",
      "North 24 Parganas", "Paschim Bardhaman", "Paschim Medinipur",
      "Purba Bardhaman", "Purba Medinipur", "Purulia", "South 24 Parganas",
      "Uttar Dinajpur",
    ],
  },
];

/** Flat list of state names for easy validation. */
export const INDIA_STATE_NAMES: string[] = INDIA_STATES.map((s) => s.name);

/** Get districts for a given state name. Returns [] if not found. */
export function getDistricts(stateName: string): string[] {
  return INDIA_STATES.find((s) => s.name === stateName)?.districts ?? [];
}
