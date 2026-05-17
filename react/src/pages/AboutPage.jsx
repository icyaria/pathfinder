import Nav from '../components/Nav'
import one from '../assets/one.jpg'
import two from '../assets/two.jpg'
import three from '../assets/three.jpg'
import four from '../assets/four.jpg'
import './AboutPage.css'

const TEAM = [
  { name: 'Maria Kapaki',   email: 'email1@example.com' },
  { name: 'Despoina Kampiwti',   email: 'email2@example.com' },
  { name: 'Kwnstantinos Katrakis', email: 'email3@example.com' },
  { name: 'Kyriaki kalamari',  email: 'email4@example.com' },
]

export default function AboutPage() {
  return (
    <div className="about-page">
      <Nav />
      <div className="about-content">
        <h1 className="about-title">About Us</h1>
        <p className="about-lead">
          We are a team passionate about connecting people with Greece's incredible trail network — sustainably and thoughtfully.
        </p>
        <div className="about-team">
          {TEAM.map((member, i) => (
            <div key={i} className="about-card">
              <h2 className="about-name">{member.name}</h2>
              <a className="about-email" href={`mailto:${member.email}`}>{member.email}</a>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
